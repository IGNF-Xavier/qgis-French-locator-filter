# standard library
import json
from typing import Optional

# PyQGIS
from qgis.core import Qgis, QgsCoordinateReferenceSystem, QgsJsonUtils, QgsRectangle

# project
from french_locator_filter.core.geocoder.rest_api_geocoder import RestAPIGeocoder


class GpfRestApiGeocoder(RestAPIGeocoder):
    """Abstract class for geocoders hitting the Géoplateforme geocodage host
    (data.geopf.fr). Shares a single class-level rate-limit counter across all
    subclasses so the documented 50 req/s per IP limit is respected even when
    several geocoders (address, parcel, poi, ...) hit the host concurrently."""

    _last_request_timestamp: int = 0

    def __init__(self):
        super().__init__()
        self.max_request_per_second = 50

    def set_last_request_timestamp(self, timestamp: int) -> None:
        """Define timestamp for last request

        :param timestamp: request timestamp
        :type timestamp: int
        """
        GpfRestApiGeocoder._last_request_timestamp = timestamp

    def last_request_timestamp(self) -> int:
        """Get last request timestamp

        :return: last request timestamp
        :rtype: int
        """
        return GpfRestApiGeocoder._last_request_timestamp

    def viewport_from_truegeometry(
        self, properties: dict, crs: QgsCoordinateReferenceSystem
    ) -> Optional[QgsRectangle]:
        """Compute a viewport from a result's real geometry (truegeometry), when
        the Géoplateforme response includes one (parcel, poi indexes)

        :param properties: response properties
        :type properties: dict
        :param crs: geometry crs
        :type crs: QgsCoordinateReferenceSystem
        :return: bounding box of the real geometry, None if not available
        :rtype: Optional[QgsRectangle]
        """
        truegeometry = properties.get("truegeometry")
        if not truegeometry:
            return None
        try:
            geojson_feature = json.dumps(
                {"type": "Feature", "geometry": truegeometry, "properties": {}}
            )
            features = QgsJsonUtils.stringToFeatureList(geojson_feature)
            if features and features[0].hasGeometry():
                return features[0].geometry().boundingBox()
        except Exception as err:
            self.log(
                message=self.tr(
                    "Impossible de calculer l'emprise du résultat : {}".format(err)
                ),
                log_level=Qgis.MessageLevel.NoLevel,
            )
        return None
