#! python3  # noqa: E265

"""
Small reusable client for the Géoplateforme WFS service, used to query the
BAN-PLUS link layers (address <-> building <-> parcel) and the PCI
"parcellaire express" layer for real parcel geometries.
"""

# standard library
import json
import time
from typing import List, Optional
from urllib.parse import quote

# PyQGIS
from qgis.core import QgsFeedback
from qgis.PyQt.QtCore import QDateTime

# project
from french_locator_filter.toolbelt.log_handler import PlgLogger
from french_locator_filter.toolbelt.network_manager import NetworkRequestsManager
from french_locator_filter.toolbelt.preferences import PlgOptionsManager


class WfsClient:
    """Client for the Géoplateforme WFS service (GetFeature, GeoJSON output).

    Holds a shared class-level rate-limit counter, since the WFS is a
    separate host/backend from the geocodage and RNB APIs (no documented
    rate limit found; kept conservative).
    """

    _last_request_timestamp: int = 0
    max_request_per_second = 10

    def __init__(self):
        self.log = PlgLogger().log
        self.plg_settings = PlgOptionsManager.get_plg_settings()

    def _wait_for_rate_limit(self, feedback: Optional[QgsFeedback] = None) -> bool:
        """Wait until the rate limit allows a new request

        :param feedback: feedback, used to detect cancellation
        :type feedback: Optional[QgsFeedback]
        :return: True if canceled while waiting, False otherwise
        :rtype: bool
        """
        while (
            QDateTime.currentMSecsSinceEpoch() - WfsClient._last_request_timestamp
            < 1000 / self.max_request_per_second
        ):
            time.sleep(0.05)
            if feedback and feedback.isCanceled():
                return True
        return False

    def get_features(
        self,
        typename: str,
        cql_filter: Optional[str] = None,
        bbox: Optional[str] = None,
        count: int = 100,
        feedback: Optional[QgsFeedback] = None,
    ) -> List[dict]:
        """Fetch features (as GeoJSON) from a WFS layer, filtered by CQL and/or bbox.

        :param typename: WFS type name (e.g. "BAN-PLUS:lien_adresse_parcelle")
        :type typename: str
        :param cql_filter: CQL filter expression (e.g. "id_adr='75104_...'"), defaults to None
        :type cql_filter: Optional[str], optional
        :param bbox: bbox filter, "miny,minx,maxy,maxx,urn:ogc:def:crs:EPSG::4326"
            (axis order matches the Géoplateforme WFS: latitude, longitude), defaults to None
        :type bbox: Optional[str], optional
        :param count: maximum number of features to fetch, defaults to 100
        :type count: int, optional
        :param feedback: feedback, used to detect cancellation, defaults to None
        :type feedback: Optional[QgsFeedback], optional
        :return: list of GeoJSON features ({"type", "geometry", "properties"})
        :rtype: List[dict]
        """
        if self._wait_for_rate_limit(feedback):
            return []

        query = (
            "SERVICE=WFS&VERSION=2.0.0&REQUEST=GetFeature"
            f"&TYPENAMES={quote(typename, safe='')}"
            f"&OUTPUTFORMAT={quote('application/json', safe='')}"
            f"&COUNT={count}"
        )
        if cql_filter:
            query += f"&CQL_FILTER={quote(cql_filter, safe='')}"
        if bbox:
            query += f"&BBOX={quote(bbox, safe=',:')}"

        try:
            qntwk = NetworkRequestsManager()
            qurl = qntwk.build_url(
                request_url=self.plg_settings.wfs_url, request_url_query=query
            )
            response_content = qntwk.get_url(url=qurl)
            data = json.loads(str(response_content, "UTF8"))
            return data.get("features", [])
        except Exception as err:
            self.log(
                message=f"Erreur lors de la demande WFS ({typename}) : {err}",
                log_level=1,
            )
            return []
        finally:
            WfsClient._last_request_timestamp = QDateTime.currentMSecsSinceEpoch()
