#! python3  # noqa: E265

"""
    Plugin settings dialog.
"""

# standard
from functools import partial
from pathlib import Path

# PyQGIS
from qgis.core import QgsApplication
from qgis.gui import QgsOptionsPageWidget, QgsOptionsWidgetFactory
from qgis.PyQt import uic
from qgis.PyQt.Qt import QUrl
from qgis.PyQt.QtGui import QDesktopServices, QIcon

# project
from french_locator_filter.__about__ import (
    DIR_PLUGIN_ROOT,
    __title__,
    __uri_homepage__,
    __uri_tracker__,
    __version__,
)
from french_locator_filter.toolbelt import PlgLogger, PlgOptionsManager
from french_locator_filter.toolbelt.preferences import PlgSettingsStructure

# ############################################################################
# ########## Globals ###############
# ##################################

FORM_CLASS, FORM_BASE = uic.loadUiType(
    Path(__file__).parent / "{}.ui".format(Path(__file__).stem)
)

# ############################################################################
# ########## Classes ###############
# ##################################


class ConfigOptionsPage(FORM_CLASS, QgsOptionsPageWidget):
    """Settings form embedded into QGIS 'options' menu."""

    def __init__(self, parent):
        """Constructor."""
        super().__init__(parent)
        self.log = PlgLogger().log
        self.plg_settings = PlgOptionsManager()
        self.setupUi(self)
        self.setObjectName("mOptionsPage{}".format(__title__))

        # header
        self.lbl_title.setText(f"{__title__} - Version {__version__}")

        # customization
        self.btn_help.setIcon(QIcon(QgsApplication.iconPath("mActionHelpContents.svg")))
        self.btn_help.pressed.connect(
            partial(QDesktopServices.openUrl, QUrl(__uri_homepage__))
        )

        self.btn_report.setIcon(
            QIcon(QgsApplication.iconPath("console/iconSyntaxErrorConsole.svg"))
        )
        self.btn_report.pressed.connect(
            partial(
                QDesktopServices.openUrl,
                QUrl(f"{__uri_tracker__}/new?issuable_template=bug_report"),
            )
        )

        self.btn_reset.setIcon(QIcon(QgsApplication.iconPath("mActionUndo.svg")))
        self.btn_reset.pressed.connect(self.reset_settings)

        # load previously saved settings
        self.load_settings()

    def apply(self):
        """Called to permanently apply the settings shown in the options page (e.g. \
        save them to QgsSettings objects). This is usually called when the options \
        dialog is accepted."""
        new_settings = PlgSettingsStructure(
            # features
            min_search_length=self.sbx_min_search_length.value(),
            search_terms_to_ignore=tuple(
                self.lne_search_terms_to_ignore.text().split(",")
            ),
            # misc
            debug_mode=self.opt_debug.isChecked(),
            version=__version__,
        )

        # dump new settings into QgsSettings
        self.plg_settings.save_from_object(new_settings)

        self.log(
            message="DEBUG - Settings successfully saved.",
            log_level=4,
        )

    def load_settings(self) -> dict:
        """Load options from QgsSettings into UI form."""
        settings = self.plg_settings.get_plg_settings()

        # features
        self.lbl_url_path_value.setText(settings.request_url)
        self.lbl_url_query_value.setText(settings.request_url_query)
        self.lbl_http_content_type_value.setText(settings.http_content_type)
        self.lbl_http_user_agent_value.setText(settings.http_user_agent)
        self.lne_search_terms_to_ignore.setText(
            ",".join(settings.search_terms_to_ignore)
        )
        self.sbx_min_search_length.setValue(settings.min_search_length)

        # misc
        self.opt_debug.setChecked(settings.debug_mode)
        self.lbl_version_saved_value.setText(settings.version)

    def reset_settings(self):
        """Reset settings to default values (set in preferences.py module)."""
        default_settings = PlgSettingsStructure()

        # dump default settings into QgsSettings
        self.plg_settings.save_from_object(default_settings)

        # update the form
        self.load_settings()

    def helpKey(self) -> str:
        """Returns the optional help key for the options page. The default
            implementation returns an empty string. If a non-empty string is returned by
            this method, it will be used as the help key retrieved when the “help”
            button is clicked while this options page is active. If an empty string is
            returned by this method the default QGIS options help will be retrieved.

        :return: help page to open
        :rtype: str
        """
        return "usage/fr_how_to_use"


class PlgOptionsFactory(QgsOptionsWidgetFactory):
    def __init__(self):
        super().__init__()

    def icon(self):
        return QIcon(str(DIR_PLUGIN_ROOT / "resources/images/icon.svg"))

    def createWidget(self, parent):
        return ConfigOptionsPage(parent)

    def title(self):
        return __title__

    def helpId(self) -> str:
        return __uri_homepage__
