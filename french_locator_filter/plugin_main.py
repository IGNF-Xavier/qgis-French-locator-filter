#! python3  # noqa: E265

"""
Main plugin module.
"""

# standard library
from pathlib import Path

# PyQGIS
from qgis.core import Qgis, QgsApplication, QgsSettings
from qgis.PyQt.QtCore import QCoreApplication, QLocale, QTranslator
from qgis.utils import iface

# project
from french_locator_filter.__about__ import (
    DIR_PLUGIN_ROOT,
    __title__,
    __uri_homepage__,
    __version__,
)
from french_locator_filter.core.locator_filter.addok_ban_fr_locator_filter import (
    FrenchBanGeocoderLocatorFilter,
)
from french_locator_filter.core.locator_filter.photon_locator_filter import (
    PhotonGeocoderLocatorFilter,
)
from french_locator_filter.gui.dlg_settings import PlgOptionsFactory
from french_locator_filter.processing.provider import FrenchLocatorProcessingProvider
from french_locator_filter.toolbelt import PlgLogger

# ############################################################################
# ########## Classes ###############
# ##################################


class FrenchGeocoderLocatorFilterPlugin:
    def __init__(self):
        """Constructor."""
        self.log = PlgLogger().log
        self.provider = None
        self.ban_locator_filter = None
        self.photon_locator_filter = None
        self.options_factory = None

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

        # -- Processing
        self.initProcessing()

    def initProcessing(self):
        """Init processing without GUI"""
        self.provider = FrenchLocatorProcessingProvider()
        QgsApplication.processingRegistry().addProvider(self.provider)

    def unload(self):
        """Cleans up when plugin is disabled/uninstalled."""
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

        if self.provider:
            QgsApplication.processingRegistry().removeProvider(self.provider)

    def tr(self, message):
        """Get the translation for a string using Qt translation API.
        We implement this ourselves since we do not inherit QObject.

        :param message: String for translation.
        :type message: str, QString

        :returns: Translated version of message.
        :rtype: QString
        """
        return QCoreApplication.translate(self.__class__.__name__, message)
