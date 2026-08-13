#! python3  # noqa: E265

"""
Main plugin module.
"""

# standard library
from functools import partial
from pathlib import Path
from typing import Optional

from qgis.core import (
    Qgis,
    QgsApplication,
    QgsCoordinateReferenceSystem,
    QgsPointXY,
    QgsSettings,
)

# PyQGIS
from qgis.gui import QgisInterface
from qgis.PyQt.QtCore import QCoreApplication, QLocale, Qt, QTranslator, QUrl
from qgis.PyQt.QtGui import QDesktopServices, QIcon
from qgis.PyQt.QtWidgets import QAction, QDockWidget, QMenu, QWidget
from qgis.utils import iface

# project
from french_locator_filter.__about__ import (
    DIR_PLUGIN_ROOT,
    __icon_path__,
    __title__,
    __uri_homepage__,
    __version__,
)
from french_locator_filter.core.locator_filter.addok_ban_fr_locator_filter import (
    FrenchBanGeocoderLocatorFilter,
)
from french_locator_filter.core.locator_filter.gpf_chained_locator_filter import (
    GpfChainedGeocoderLocatorFilter,
)
from french_locator_filter.core.locator_filter.gpf_dynamic_locator_filter import (
    GpfDynamicGeocoderLocatorFilter,
)
from french_locator_filter.core.locator_filter.gpf_parcel_locator_filter import (
    GpfParcelGeocoderLocatorFilter,
)
from french_locator_filter.core.locator_filter.gpf_rnb_locator_filter import (
    GpfRnbGeocoderLocatorFilter,
)
from french_locator_filter.core.locator_filter.photon_locator_filter import (
    PhotonGeocoderLocatorFilter,
)
from french_locator_filter.gui.dlg_settings import PlgOptionsFactory
from french_locator_filter.gui.wdg_parcel_search import ParcelSearchWidget
from french_locator_filter.gui.wdg_reverse_geocoding import ReverseGeocodingWidget
from french_locator_filter.processing.provider import FrenchLocatorProcessingProvider
from french_locator_filter.processing.utils import (
    create_processing_action,
)
from french_locator_filter.toolbelt import PlgLogger
from french_locator_filter.toolbelt.rnb_tile_layer import add_rnb_vector_tile_layer

# ############################################################################
# ########## Classes ###############
# ##################################


class FrenchGeocoderLocatorFilterPlugin:
    def __init__(self, iface: QgisInterface):
        """Constructor.

        :param iface: An interface instance that will be passed to this class which \
        provides the hook by which you can manipulate the QGIS application at run time.
        :type iface: QgsInterface
        """
        self.iface = iface
        self.log = PlgLogger().log
        self.provider = None
        self.ban_locator_filter = None
        self.photon_locator_filter = None
        self.parcel_locator_filter = None
        self.rnb_locator_filter = None
        self.dynamic_locator_filter = None
        self.chained_locator_filter = None
        self.options_factory = None

        self.docks = []
        self.actions = []

        self.action_help: Optional[QAction] = None
        self.action_settings: Optional[QAction] = None
        self.action_geocoding: Optional[QAction] = None
        self.action_reverse_geocoding: Optional[QAction] = None
        self.reverse_geocoding_widget_action: Optional[QAction] = None
        self.parcel_search_widget_action: Optional[QAction] = None

        self.action_help_plugin_menu_documentation: Optional[QAction] = None
        self.action_add_rnb_layer: Optional[QAction] = None

        # translation
        self.locale: str = QgsSettings().value("locale/userLocale", QLocale().name())[
            0:2
        ]
        locale_path: Path = (
            DIR_PLUGIN_ROOT / f"resources/i18n/french_locator_filter_{self.locale}.qm"
        )
        if locale_path.exists():
            self.translator = QTranslator()
            self.translator.load(str(locale_path.resolve()))
            QCoreApplication.installTranslator(self.translator)
            self.log(
                message=f"Translation loaded from file: {self.locale}, {locale_path}",
                log_level=Qgis.MessageLevel.NoLevel,
            )
        else:
            self.log(
                message=f"Translation file does not exist: {self.locale}, {locale_path}",
                log_level=Qgis.MessageLevel.Warning,
            )

        self._title_menu: str = self.tr("French Geocoder")

        self.log(
            message=(
                "DEBUG - French (BAN Geocoder) Locator Filter"
                f" ({__title__} {__version__}) installed."
            ),
            log_level=Qgis.MessageLevel.NoLevel,
        )

    def initGui(self):
        """Set up plugin UI elements."""
        # settings page within the QGIS preferences menu
        if not self.options_factory:
            self.options_factory = PlgOptionsFactory()
            iface.registerOptionsWidgetFactory(self.options_factory)

            # Add search path for plugin
            help_search_paths = QgsSettings().value("help/helpSearchPath")
            if (
                isinstance(help_search_paths, list)
                and __uri_homepage__ not in help_search_paths
            ):
                help_search_paths.append(__uri_homepage__)
            else:
                help_search_paths = [help_search_paths, __uri_homepage__]
            QgsSettings().setValue("help/helpSearchPath", help_search_paths)

        # locator
        if not self.ban_locator_filter:
            self.ban_locator_filter = FrenchBanGeocoderLocatorFilter(
                canvas=iface.mapCanvas()
            )
            iface.registerLocatorFilter(self.ban_locator_filter)

        if not self.photon_locator_filter:
            self.photon_locator_filter = PhotonGeocoderLocatorFilter(
                canvas=iface.mapCanvas()
            )
            iface.registerLocatorFilter(self.photon_locator_filter)

        if not self.parcel_locator_filter:
            self.parcel_locator_filter = GpfParcelGeocoderLocatorFilter(
                canvas=iface.mapCanvas()
            )
            iface.registerLocatorFilter(self.parcel_locator_filter)

        if not self.rnb_locator_filter:
            self.rnb_locator_filter = GpfRnbGeocoderLocatorFilter(
                canvas=iface.mapCanvas()
            )
            iface.registerLocatorFilter(self.rnb_locator_filter)

        if not self.dynamic_locator_filter:
            self.dynamic_locator_filter = GpfDynamicGeocoderLocatorFilter(
                canvas=iface.mapCanvas()
            )
            iface.registerLocatorFilter(self.dynamic_locator_filter)

        if not self.chained_locator_filter:
            self.chained_locator_filter = GpfChainedGeocoderLocatorFilter(
                canvas=iface.mapCanvas()
            )
            iface.registerLocatorFilter(self.chained_locator_filter)

        # -- Actions
        self.action_help = QAction(
            QgsApplication.getThemeIcon("mActionHelpContents.svg"),
            self.tr("Help"),
            self.iface.mainWindow(),
        )
        self.action_help.triggered.connect(
            partial(QDesktopServices.openUrl, QUrl(__uri_homepage__))
        )

        self.action_settings = QAction(
            QgsApplication.getThemeIcon("console/iconSettingsConsole.svg"),
            self.tr("Settings"),
            self.iface.mainWindow(),
        )
        self.action_settings.triggered.connect(
            lambda: self.iface.showOptionsDialog(
                currentPage="mOptionsPage{}".format(__title__)
            )
        )

        # -- Menu

        # -- Processing
        self.initProcessing()

        # Create widget for itinerary
        reverse_geocoding_widget = ReverseGeocodingWidget(self.iface.mainWindow())
        # Define default position
        reverse_geocoding_widget.wdg_selection.set_crs(
            QgsCoordinateReferenceSystem("EPSG:4326")
        )
        reverse_geocoding_widget.wdg_selection.set_display_point(
            QgsPointXY(2.42412, 48.84572)
        )

        self.reverse_geocoding_widget_action = self.add_dock_widget_and_action(
            title=self.tr("Géocodage inversé"),
            name="reverse_geocode",
            widget=reverse_geocoding_widget,
        )

        # Create widget for structured parcel search
        parcel_search_widget = ParcelSearchWidget(self.iface.mainWindow())
        self.parcel_search_widget_action = self.add_dock_widget_and_action(
            title=self.tr("Recherche de parcelle"),
            name="parcel_search",
            widget=parcel_search_widget,
        )

        self.action_geocoding = self._create_geocoding_action(
            self.iface.mainWindow(), only_gpf=False
        )
        self.iface.addPluginToMenu(self._title_menu, self.action_geocoding)

        self.action_reverse_geocoding = self._create_reverse_geocoding_action(
            self.iface.mainWindow(), only_gpf=False
        )
        self.iface.addPluginToMenu(self._title_menu, self.action_reverse_geocoding)

        self.action_add_rnb_layer = QAction(
            self.tr("Ajouter la couche RNB (bâtiments)"),
            self.iface.mainWindow(),
        )
        self.action_add_rnb_layer.triggered.connect(add_rnb_vector_tile_layer)
        self.iface.addPluginToMenu(self._title_menu, self.action_add_rnb_layer)

        self.iface.addPluginToMenu(self._title_menu, self.action_settings)
        self.iface.addPluginToMenu(self._title_menu, self.action_help)

        # -- Help menu

        # documentation
        self.iface.pluginHelpMenu().addSeparator()
        self.action_help_plugin_menu_documentation = QAction(
            QIcon(str(__icon_path__)),
            f"{__title__} - Documentation",
            self.iface.mainWindow(),
        )
        self.action_help_plugin_menu_documentation.triggered.connect(
            partial(QDesktopServices.openUrl, QUrl(__uri_homepage__))
        )

        self.iface.pluginHelpMenu().addAction(
            self.action_help_plugin_menu_documentation
        )

    def add_dock_widget_and_action(
        self, title: str, name: str, widget: QWidget
    ) -> QAction:
        """Add widget display as QDockWidget with an QAction in plugin toolbar


        :param name: dockwidget name for position save
        :type name: str
        :param widget: widget to insert
        :type widget: QWidget
        """

        # Create dockwidget
        dock = QDockWidget(title, iface.mainWindow())
        dock.setObjectName(name)
        dock.setWindowIcon(widget.windowIcon())

        # Add widget
        dock.setWidget(widget)

        # Add to QGIS
        iface.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, dock)

        # Default close
        dock.close()

        # Append to dock list for unload
        self.docks.append(dock)
        dock.toggleViewAction().setIcon(widget.windowIcon())

        # Append to action list for unload
        action = dock.toggleViewAction()
        self.actions.append(action)

        # Add action to toolbar
        iface.addToolBarIcon(action)

        return action

    def _create_geocoding_action(self, parent: QWidget, only_gpf: bool) -> QAction:
        """Create action with menu for geocoding related function actions

        :param parent: parent widget
        :type parent: QWidget
        :param only_gpf: add only action with Géoplateforme use
        :type only_gpf: bool
        :return: action for geocoding
        :rtype: QAction
        """
        # Geocoding action
        geocoding_action = QAction(
            self.tr("Géocodage"),
            parent,
        )
        geocoding_menu = QMenu(parent)

        if self.parcel_search_widget_action:
            geocoding_menu.addAction(self.parcel_search_widget_action)

        # Geocoding Processings
        geocoding_action_processing = QAction(self.tr("Traitements"), parent)
        geocoding_menu_processing = QMenu(parent)
        geocoding_menu_processing.addAction(
            create_processing_action(
                "french_locator_filter:gpf_geocoder_batch",
                geocoding_menu_processing,
            )
        )
        geocoding_menu_processing.addAction(
            create_processing_action(
                "french_locator_filter:gpf_parcel_geocoder_batch",
                geocoding_menu_processing,
            )
        )
        geocoding_menu_processing.addAction(
            create_processing_action(
                "french_locator_filter:gpf_rnb_geocoder_batch",
                geocoding_menu_processing,
            )
        )
        geocoding_menu_processing.addAction(
            create_processing_action(
                "french_locator_filter:gpf_dynamic_geocoder_batch",
                geocoding_menu_processing,
            )
        )
        geocoding_menu_processing.addAction(
            create_processing_action(
                "french_locator_filter:gpf_chained_geocoder_batch",
                geocoding_menu_processing,
            )
        )

        if not only_gpf:
            geocoding_menu_processing.addAction(
                create_processing_action(
                    "french_locator_filter:photon_geocoder_batch",
                    geocoding_menu_processing,
                )
            )

        geocoding_action_processing.setMenu(geocoding_menu_processing)

        geocoding_menu.addAction(geocoding_action_processing)

        geocoding_action.setMenu(geocoding_menu)
        return geocoding_action

    def _create_reverse_geocoding_action(
        self, parent: QWidget, only_gpf: bool
    ) -> QAction:
        """Create action with menu for reverse geocoding related function actions

        :param parent: parent widget
        :type parent: QWidget
        :param only_gpf: add only action with Géoplateforme use
        :type only_gpf: bool
        :return: action for geocoding
        :rtype: QAction
        """

        # Reverse Geocoding action
        reverse_geocoding_action = QAction(
            self.tr("Géocodage inversé"),
            parent,
        )
        reverse_geocoding_menu = QMenu(parent)

        reverse_geocoding_menu.addAction(self.reverse_geocoding_widget_action)

        # Reverse Geocoding Processings
        reverse_geocoding_action_processing = QAction(self.tr("Traitements"), parent)
        reverse_geocoding_menu_processing = QMenu(parent)
        reverse_geocoding_menu_processing.addAction(
            create_processing_action(
                "french_locator_filter:gpf_inverse_geocoder_batch",
                reverse_geocoding_menu_processing,
            )
        )
        reverse_geocoding_menu_processing.addAction(
            create_processing_action(
                "french_locator_filter:gpf_parcel_inverse_geocoder_batch",
                reverse_geocoding_menu_processing,
            )
        )
        reverse_geocoding_menu_processing.addAction(
            create_processing_action(
                "french_locator_filter:gpf_rnb_inverse_geocoder_batch",
                reverse_geocoding_menu_processing,
            )
        )
        reverse_geocoding_menu_processing.addAction(
            create_processing_action(
                "french_locator_filter:gpf_dynamic_inverse_geocoder_batch",
                reverse_geocoding_menu_processing,
            )
        )
        reverse_geocoding_menu_processing.addAction(
            create_processing_action(
                "french_locator_filter:gpf_chained_inverse_geocoder_batch",
                reverse_geocoding_menu_processing,
            )
        )

        if not only_gpf:
            reverse_geocoding_menu_processing.addAction(
                create_processing_action(
                    "french_locator_filter:photon_inverse_geocoder_batch",
                    reverse_geocoding_menu_processing,
                )
            )

        reverse_geocoding_action_processing.setMenu(reverse_geocoding_menu_processing)

        reverse_geocoding_menu.addAction(reverse_geocoding_action_processing)

        reverse_geocoding_action.setMenu(reverse_geocoding_menu)

        return reverse_geocoding_action

    def create_gpf_plugins_actions(self, parent: QWidget) -> list[QAction]:
        """Create action to be inserted a Geoplateforme plugin

        :param parent: parent widget
        :type parent: QWidget
        :return: list of action to add in Geoplateforme plugin
        :rtype: list[QAction]
        """
        available_actions = []

        available_actions.append(self._create_geocoding_action(parent, only_gpf=True))
        available_actions.append(
            self._create_reverse_geocoding_action(parent, only_gpf=True)
        )
        return available_actions

    def initProcessing(self):
        """Init processing without GUI"""
        self.provider = FrenchLocatorProcessingProvider()
        QgsApplication.processingRegistry().addProvider(self.provider)

    def unload(self):
        """Cleans up when plugin is disabled/uninstalled."""
        for _actions in self.actions:
            self.iface.removeToolBarIcon(_actions)
            del _actions
        for _dock in self.docks:
            self.iface.removeDockWidget(_dock)
            _dock.deleteLater()
        self.docks.clear()

        # -- Clean up menu
        self.iface.removePluginMenu(self._title_menu, self.action_help)
        self.iface.removePluginMenu(self._title_menu, self.action_settings)
        if self.action_reverse_geocoding:
            self.iface.removePluginMenu(self._title_menu, self.action_reverse_geocoding)
        if self.action_geocoding:
            self.iface.removePluginMenu(self._title_menu, self.action_geocoding)
        if self.action_add_rnb_layer:
            self.iface.removePluginMenu(self._title_menu, self.action_add_rnb_layer)

        # -- Clean up preferences panel in QGIS settings
        self.iface.unregisterOptionsWidgetFactory(self.options_factory)

        # remove from QGIS help/extensions menu
        if self.action_help_plugin_menu_documentation:
            self.iface.pluginHelpMenu().removeAction(
                self.action_help_plugin_menu_documentation
            )

        # remove actions
        del self.action_settings
        del self.action_help

        # -- Clean up preferences panel in QGIS settings
        if self.options_factory:
            iface.unregisterOptionsWidgetFactory(self.options_factory)
            # pop from help path
            help_search_paths = QgsSettings().value("help/helpSearchPath")
            if (
                isinstance(help_search_paths, list)
                and __uri_homepage__ in help_search_paths
            ):
                help_search_paths.remove(__uri_homepage__)
            QgsSettings().setValue("help/helpSearchPath", help_search_paths)

        # remove filter from locator
        if self.ban_locator_filter:
            iface.deregisterLocatorFilter(self.ban_locator_filter)

        # remove filter from locator
        if self.photon_locator_filter:
            iface.deregisterLocatorFilter(self.photon_locator_filter)

        # remove filter from locator
        if self.parcel_locator_filter:
            iface.deregisterLocatorFilter(self.parcel_locator_filter)

        # remove filter from locator
        if self.rnb_locator_filter:
            iface.deregisterLocatorFilter(self.rnb_locator_filter)

        # remove filter from locator
        if self.dynamic_locator_filter:
            iface.deregisterLocatorFilter(self.dynamic_locator_filter)

        # remove filter from locator
        if self.chained_locator_filter:
            iface.deregisterLocatorFilter(self.chained_locator_filter)

        if self.provider:
            QgsApplication.processingRegistry().removeProvider(self.provider)
            self.provider = None

    def tr(self, message):
        """Get the translation for a string using Qt translation API.
        We implement this ourselves since we do not inherit QObject.

        :param message: String for translation.
        :type message: str, QString

        :returns: Translated version of message.
        :rtype: QString
        """
        return QCoreApplication.translate(self.__class__.__name__, message)
