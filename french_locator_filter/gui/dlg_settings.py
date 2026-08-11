#! python3  # noqa: E265

"""
Plugin settings dialog.
"""

# standard
import os
from dataclasses import asdict
from functools import partial
from pathlib import Path
from typing import Union

# PyQGIS
from qgis.core import Qgis, QgsApplication
from qgis.gui import QgsFilterLineEdit, QgsOptionsPageWidget, QgsOptionsWidgetFactory
from qgis.PyQt import uic
from qgis.PyQt.QtCore import Qt, QUrl
from qgis.PyQt.QtGui import QDesktopServices, QIcon
from qgis.PyQt.QtWidgets import QCheckBox, QLabel, QListWidgetItem, QSpinBox

# project
from french_locator_filter.__about__ import (
    DIR_PLUGIN_ROOT,
    __title__,
    __uri_homepage__,
    __uri_tracker__,
    __version__,
)
from french_locator_filter.toolbelt import PlgLogger, PlgOptionsManager
from french_locator_filter.toolbelt.geocodage_capabilities import (
    fetch_and_cache_capabilities,
    load_capabilities,
)
from french_locator_filter.toolbelt.preferences import (
    PlgEnvVariableSettings,
    PlgSettingsStructure,
)

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

        self.btn_refresh_indexes.pressed.connect(self._refresh_indexes)

        # load previously saved settings
        self.load_settings()

    def _populate_indexes_list(self, active_indexes: list) -> None:
        """Populate the Géoplateforme indexes list widget from the (bundled or
        cached) capabilities, checking items currently active.

        :param active_indexes: ids of currently active indexes
        :type active_indexes: list
        """
        self.lsw_indexes.clear()
        capabilities = load_capabilities()
        for index in capabilities.get("indexes", []):
            item = QListWidgetItem(index.get("id"))
            item.setToolTip(index.get("description", ""))
            item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
            item.setCheckState(
                Qt.CheckState.Checked
                if index.get("id") in active_indexes
                else Qt.CheckState.Unchecked
            )
            self.lsw_indexes.addItem(item)

    def _refresh_indexes(self) -> None:
        """Fetch capabilities from the live service and repopulate the indexes
        list, keeping the currently checked indexes checked when still available.
        """
        currently_checked = [
            self.lsw_indexes.item(row).text()
            for row in range(self.lsw_indexes.count())
            if self.lsw_indexes.item(row).checkState() == Qt.CheckState.Checked
        ]
        try:
            fetch_and_cache_capabilities()
        except Exception as err:
            self.log(
                message=self.tr(
                    "Impossible de rafraîchir les index depuis le service : {}"
                ).format(err),
                log_level=Qgis.MessageLevel.Warning,
            )
        self._populate_indexes_list(currently_checked)

    @property
    def attribute_widget_dict(
        self,
    ) -> dict[str, Union[QgsFilterLineEdit, QLabel, QSpinBox, QCheckBox]]:
        """Get attribute widget dict.
        This is a dict of widget used for settings attribute definition

        :return: _description_
        :rtype: dict[str, QgsFilterLineEdit]
        """
        return {
            "http_content_type": self.lbl_http_content_type_value,
            "http_user_agent": self.lbl_http_user_agent_value,
            "min_search_length": self.sbx_min_search_length,
            "request_url": self.lbl_url_path_value,
            "request_url_query": self.lbl_url_query_value,
            "request_photon_url": self.lne_url_api_photon_path_value,
            "request_photon_url_query": self.lne_url_api_photon_query_value,
            "request_rnb_url": self.lne_url_api_rnb_path_value,
            "debug_mode": self.opt_debug,
        }

    def set_attribute_with_env_variable(
        self,
        attribute: str,
        settings: PlgSettingsStructure,
        widget: Union[QgsFilterLineEdit, QLabel, QSpinBox, QCheckBox],
    ) -> None:
        """Set attribut in widget with check if environnement variable is used

        :param attribute: settings attribute name
        :type attribute: str
        :param settings: settings containing attribute
        :type settings: PlgSettingsStructure
        :param widget: widget to store attribute
        :type widget: QgsFilterLineEdit
        """
        value = asdict(settings)[attribute]

        type_widget = type(widget)
        if type_widget in [QgsFilterLineEdit, QSpinBox]:
            widget.setValue(value)
        if type_widget in [QLabel]:
            widget.setText(value)
        if type_widget is QCheckBox:
            widget.setChecked(value)

        env_variable_settings = PlgEnvVariableSettings()
        env_variable = env_variable_settings.env_variable_used(attribute)
        if env_variable and os.getenv(env_variable):
            widget.setEnabled(False)
            widget.setToolTip(
                self.tr("Value defined from '{}' environnement variable").format(
                    env_variable
                )
            )
        else:
            widget.setEnabled(True)

    @staticmethod
    def set_setting_attribute_from_widget(
        settings: PlgSettingsStructure,
        attribute: str,
        widget: Union[QgsFilterLineEdit, QLabel, QSpinBox, QCheckBox],
    ) -> None:
        """Define settings attribute from widget

        Args:
            settings (PlgSettingsStructure): settings
            attribute (str): attribute
            widget (Union[QgsFilterLineEdit, QLabel, QSpinBox, QCheckBox]): widget to read value
        """
        type_widget = type(widget)
        if type_widget in [QgsFilterLineEdit, QSpinBox]:
            value = widget.value()
        if type_widget in [QLabel]:
            value = widget.text()
        if type_widget is QCheckBox:
            value = widget.isChecked()

        setattr(settings, attribute, value)

    def apply(self):
        """Called to permanently apply the settings shown in the options page (e.g. \
        save them to QgsSettings objects). This is usually called when the options \
        dialog is accepted."""
        checked_indexes = [
            self.lsw_indexes.item(row).text()
            for row in range(self.lsw_indexes.count())
            if self.lsw_indexes.item(row).checkState() == Qt.CheckState.Checked
        ]

        new_settings = PlgSettingsStructure(
            # features
            search_terms_to_ignore=tuple(
                self.lne_search_terms_to_ignore.text().split(",")
            ),
            request_indexes=",".join(checked_indexes),
            version=__version__,
        )
        # Define attribute
        for attribute, widget in self.attribute_widget_dict.items():
            self.set_setting_attribute_from_widget(new_settings, attribute, widget)

        # dump new settings into QgsSettings
        self.plg_settings.save_from_object(new_settings)

        self.log(
            message="DEBUG - Settings successfully saved.",
            log_level=Qgis.MessageLevel.NoLevel,
        )

    def load_settings(self) -> dict:
        """Load options from QgsSettings into UI form."""
        settings = self.plg_settings.get_plg_settings()

        # features
        self.lne_search_terms_to_ignore.setText(
            ",".join(settings.search_terms_to_ignore)
        )
        self._populate_indexes_list(settings.request_indexes_list)

        # Define widget attribute
        for attribute, widget in self.attribute_widget_dict.items():
            self.set_attribute_with_env_variable(attribute, settings, widget)

        # misc
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
