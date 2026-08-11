#! python3  # noqa: E265

"""
Load and cache the Géoplateforme geocoding service GetCapabilities, used to
dynamically determine which indexes (address, poi, parcel, ...) are
available and what fields each of them returns.
"""

# standard library
import json
from pathlib import Path
from typing import List, Optional

# PyQGIS
from qgis.core import QgsApplication

# project
from french_locator_filter.__about__ import DIR_PLUGIN_ROOT, __title__
from french_locator_filter.toolbelt.log_handler import PlgLogger
from french_locator_filter.toolbelt.network_manager import NetworkRequestsManager
from french_locator_filter.toolbelt.preferences import PlgOptionsManager

# a minimal fallback so the plugin never breaks if no capabilities file
# (bundled or cached) can be found
_FALLBACK_CAPABILITIES = {
    "indexes": [
        {
            "id": "address",
            "description": "adresses postales",
            "fields": [
                {"name": "id"},
                {"name": "type"},
                {"name": "label"},
                {"name": "city"},
                {"name": "postcode"},
                {"name": "citycode"},
                {"name": "housenumber"},
                {"name": "street"},
                {"name": "x"},
                {"name": "y"},
                {"name": "score"},
            ],
        }
    ]
}


def bundled_capabilities_path() -> Path:
    """Path to the capabilities snapshot embedded in the plugin at packaging time

    :return: bundled capabilities file path
    :rtype: Path
    """
    return DIR_PLUGIN_ROOT / "resources" / "geocodage_capabilities.json"


def user_cache_capabilities_path() -> Path:
    """Path to the user-writable capabilities cache, refreshed from the live
    service via the settings page

    :return: cached capabilities file path
    :rtype: Path
    """
    return Path(QgsApplication.qgisSettingsDirPath()) / __title__ / "geocodage_capabilities.json"


def _load_json_file(path: Path) -> Optional[dict]:
    """Load a JSON file if it exists and is valid

    :param path: file path
    :type path: Path
    :return: parsed content, None if the file is missing or invalid
    :rtype: Optional[dict]
    """
    if not path.exists():
        return None
    try:
        with path.open(encoding="utf-8") as f:
            return json.load(f)
    except Exception as err:
        PlgLogger().log(
            message=f"Impossible de lire le fichier de capacités {path} : {err}",
            log_level=1,
        )
        return None


def load_capabilities() -> dict:
    """Load geocoding capabilities: user-refreshed cache if available, otherwise
    the snapshot bundled with the plugin, otherwise a minimal built-in fallback.

    :return: capabilities dict (at least an "indexes" key)
    :rtype: dict
    """
    return (
        _load_json_file(user_cache_capabilities_path())
        or _load_json_file(bundled_capabilities_path())
        or _FALLBACK_CAPABILITIES
    )


def fetch_and_cache_capabilities() -> dict:
    """Fetch the live GetCapabilities from the Géoplateforme geocoding service
    and store it in the user-writable cache.

    :raises Exception: if the request fails
    :return: fetched capabilities dict
    :rtype: dict
    """
    plg_settings = PlgOptionsManager.get_plg_settings()
    qntwk = NetworkRequestsManager()
    qurl = qntwk.build_url(
        request_url=f"{plg_settings.gpf_url}getcapabilities", request_url_query=""
    )
    response_content = qntwk.get_url(url=qurl)
    capabilities = json.loads(str(response_content, "UTF8"))

    cache_path = user_cache_capabilities_path()
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    with cache_path.open("w", encoding="utf-8") as f:
        json.dump(capabilities, f, indent=2, ensure_ascii=False)

    return capabilities


def get_index_fields(capabilities: dict, index_id: str) -> List[dict]:
    """Get field definitions for a given index id

    :param capabilities: capabilities dict, as returned by load_capabilities()
    :type capabilities: dict
    :param index_id: index id (e.g. "address", "poi", "parcel")
    :type index_id: str
    :return: list of field definitions ({"name": ..., "description": ..., ...}),
        empty list if the index is unknown
    :rtype: List[dict]
    """
    for index in capabilities.get("indexes", []):
        if index.get("id") == index_id:
            return index.get("fields", [])
    return []
