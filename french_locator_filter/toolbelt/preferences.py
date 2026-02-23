#! python3  # noqa: E265

"""
Plugin settings.
"""

# standard
import os
from dataclasses import asdict, dataclass, field, fields
from typing import Iterable, Tuple

# PyQGIS
from qgis.core import Qgis, QgsSettings

# package
import french_locator_filter.toolbelt.log_handler as log_hdlr
from french_locator_filter.__about__ import __title__, __version__

# ############################################################################
# ########## Classes ###############
# ##################################

PREFIX_ENV_VARIABLE = "QGIS_FRENCH_LOCATOR_"


@dataclass
class PlgEnvVariableSettings:
    """Plugin settings from environnement variable"""

    def env_variable_used(self, attribute: str, default_from_name: bool = True) -> str:
        """Get environnement variable used for environnement variable settings

        :param attribute: attribute to check
        :type attribute: str
        :param default_from_name: define default environnement value from attribute name QGIS_<upper case attribute>
        :type default_from_name: bool
        :return: environnement variable used
        :rtype: str
        """
        settings_env_variable = asdict(self)
        env_variable = settings_env_variable.get(attribute, "")
        if not env_variable and default_from_name:
            env_variable = f"{PREFIX_ENV_VARIABLE}{attribute}".upper()
        return env_variable


@dataclass
class PlgSettingsStructure:
    """Plugin settings structure and defaults values."""

    # misc
    debug_mode: bool = False
    version: str = __version__

    # network
    http_content_type: str = "application/json"
    http_user_agent: str = f"{__title__}/{__version__}"
    min_search_length: int = 3
    search_terms_to_ignore: Tuple[str] = field(default=("null", "undefined"))

    # API BAN
    request_url: str = "https://data.geopf.fr/geocodage/"
    request_url_query: str = "limit=10&autocomplete=1"

    # API Photon
    request_photon_url: str = "https://photon.komoot.io/"
    request_photon_url_query: str = "limit=10&lang=fr"

    @staticmethod
    def _url_with_trailing_slash(url: str) -> str:
        """Add trailing slash in url

        :param url: url
        :type url: str
        :return: url with trailing slash
        :rtype: str
        """
        return url if url.endswith("/") else url + "/"

    @property
    def gpf_url(self) -> str:
        """Return the URL for geoplateforme use"""
        return self._url_with_trailing_slash(self.request_url)

    @property
    def photon_url(self) -> str:
        """Return the URL for photon use"""
        return self._url_with_trailing_slash(self.request_photon_url)

    @property
    def search_terms_to_ignore_list(self) -> list:
        """Convert search_terms_to_ignore from str into list by splitting on comma and
            stripping.

        :return: list of search terms to ignore
        :rtype: list
        """
        if isinstance(self.search_terms_to_ignore, str):
            return [term.strip() for term in self.search_terms_to_ignore.split(",")]
        return self.search_terms_to_ignore

    @property
    def terms_to_str(self) -> str:
        """Convert search_terms_to_ignore from list into str separated by comma and
            space.

        :return: str separated by comma space
        :rtype: str
        """
        if isinstance(self.search_terms_to_ignore, Iterable):
            return ", ".join(self.search_terms_to_ignore)
        return self.search_terms_to_ignore


class PlgOptionsManager:
    @staticmethod
    def get_plg_settings() -> PlgSettingsStructure:
        """Load and return plugin settings as a dictionary. \
        Useful to get user preferences across plugin logic.

        :return: plugin settings
        :rtype: PlgSettingsStructure
        """
        # get dataclass fields definition
        settings_fields = fields(PlgSettingsStructure)
        env_variable_settings = PlgEnvVariableSettings()

        # retrieve settings from QGIS/Qt
        settings = QgsSettings()
        settings.beginGroup(__title__)

        # map settings values to preferences object
        li_settings_values = []
        for i in settings_fields:
            try:
                value = settings.value(key=i.name, defaultValue=i.default, type=i.type)
                # If environnement variable used, get value from environnement variable
                env_variable = env_variable_settings.env_variable_used(i.name)
                if env_variable:
                    value = os.getenv(env_variable, value)
                li_settings_values.append(value)
            except TypeError:
                li_settings_values.append(
                    settings.value(key=i.name, defaultValue=i.default)
                )

        # instanciate new settings object
        options = PlgSettingsStructure(*li_settings_values)

        settings.endGroup()

        return options

    @staticmethod
    def get_value_from_key(key: str, default=None, exp_type=None):
        """Load and return plugin settings as a dictionary. \
        Useful to get user preferences across plugin logic.

        :return: plugin settings value matching key
        """
        if not hasattr(PlgSettingsStructure, key):
            log_hdlr.PlgLogger.log(
                message="Bad settings key. Must be one of: {}".format(
                    ",".join(PlgSettingsStructure._fields)
                ),
                log_level=Qgis.MessageLevel.Warning,
            )
            return None

        settings = QgsSettings()
        settings.beginGroup(__title__)

        try:
            out_value = settings.value(key=key, defaultValue=default, type=exp_type)
        except Exception as err:
            log_hdlr.PlgLogger.log(
                message="Error occurred trying to get settings: {}.Trace: {}".format(
                    key, err
                )
            )
            out_value = None

        settings.endGroup()

        return out_value

    @classmethod
    def set_value_from_key(cls, key: str, value):
        """Load and return plugin settings as a dictionary. \
        Useful to get user preferences across plugin logic.

        :return: plugin settings value matching key
        """
        if not hasattr(PlgSettingsStructure, key):
            log_hdlr.PlgLogger.log(
                message="Bad settings key: {}. Must be one of: {}".format(
                    key, ",".join(PlgSettingsStructure._fields)
                ),
                log_level=Qgis.MessageLevel.Critical,
            )
            return False

        settings = QgsSettings()
        settings.beginGroup(__title__)

        try:
            settings.setValue(key, value)
            out_value = True
            log_hdlr.PlgLogger.log(
                f"Setting `{key}` saved with value `{value}`", log_level=4
            )
        except Exception as err:
            log_hdlr.PlgLogger.log(
                message="Error occurred trying to set settings: {}.Trace: {}".format(
                    key, err
                )
            )
            out_value = False

        settings.endGroup()

        return out_value

    @classmethod
    def save_from_object(cls, plugin_settings_obj: PlgSettingsStructure):
        """Load and return plugin settings as a dictionary. \
        Useful to get user preferences across plugin logic.

        :return: plugin settings value matching key
        """
        settings = QgsSettings()
        settings.beginGroup(__title__)

        for k, v in asdict(plugin_settings_obj).items():
            cls.set_value_from_key(k, v)

        settings.endGroup()
