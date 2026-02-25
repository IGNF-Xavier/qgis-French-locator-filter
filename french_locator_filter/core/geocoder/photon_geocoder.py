# standard library
from typing import Dict, Optional

# PyQGIS
from qgis.core import (
    Qgis,
    QgsCoordinateReferenceSystem,
    QgsFeature,
    QgsGeocoderResult,
    QgsGeometry,
    QgsPointXY,
    QgsRectangle,
)
from qgis.PyQt.QtCore import QMetaType

# project
from french_locator_filter.core.geocoder.rest_api_geocoder import RestAPIGeocoder


class PhotonGeocoder(RestAPIGeocoder):
    """Geocoder for Photon API"""

    _last_request_timestamp: int = 0

    def __init__(self):
        super().__init__()
        self.max_request_per_second = 10

    def set_last_request_timestamp(self, timestamp: int) -> int:
        """Define timestamp for last request

        :param timestamp: request timestamp
        :type timestamp: int
        """
        PhotonGeocoder._last_request_timestamp = timestamp

    def last_request_timestamp(self) -> int:
        """Get last request timestamp

        :return: last request timestamp
        :rtype: int
        """
        return PhotonGeocoder._last_request_timestamp

    @property
    def _attributes(self) -> Dict[str, QMetaType.Type]:
        """Get attributes to read from REST API properties.
        To be overriden in implementation, empty list by default

        Returns:
            Dict[str, QMetaType.Type]: dict of attribute with expected data type
        """
        return {
            "name": QMetaType.Type.QString,
            "street": QMetaType.Type.QString,
            "housenumber": QMetaType.Type.QString,
            "postcode": QMetaType.Type.QString,
            "state": QMetaType.Type.QString,
            "country": QMetaType.Type.QString,
            "countrycode": QMetaType.Type.QString,
            "osm_id": QMetaType.Type.Int,
            "osm_key": QMetaType.Type.QString,
            "osm_value": QMetaType.Type.QString,
            "osm_type": QMetaType.Type.QString,
            "city": QMetaType.Type.QString,
            "locality": QMetaType.Type.QString,
            "county": QMetaType.Type.QString,
            "type": QMetaType.Type.QString,
            "district": QMetaType.Type.QString,
        }

    def request_url(self, reverse: bool = False) -> str:
        """Define request url

        :param reverse: True for reverse geocoding, False otherwise, defaults to False
        :type reverse: bool, optional
        :raises NotImplementedError: method not implemented in derived class
        :return: request url for geocoding
        :rtype: str
        """
        url_service = self.plg_settings.photon_url
        if reverse:
            return f"{url_service}reverse"
        return f"{url_service}api"

    @property
    def request_url_query(self):
        """Define default request url query

        Returns:
            str: request url query
        """
        return self.plg_settings.request_photon_url_query

    def get_reverse_geocode_query(self, feature: QgsFeature) -> Optional[str]:
        """Get query for reverse geocode
        For point we use &lon&lat
        For all other geometry type centroid is use as point

        :param feature: input feature
        :type feature: QgsFeature
        :return: reverse geocode query, None is feature geometry is None
        :rtype: Optional[str]
        """
        geometry = feature.geometry()
        if geometry:
            if geometry.type() == Qgis.GeometryType.Point:
                point = geometry.asPoint()
                query = f"lon={point.x()}&lat={point.y()}"
            else:
                center = geometry.centroid().asPoint()
                query = f"lon={center.x()}&lat={center.y()}"
            return query
        return None

    def _result_from_json(self, response: dict) -> QgsGeocoderResult:
        """Create a QgsGeocoderResult from json content

        Args:
            response (dict): json response content

        Returns:
            QgsGeocoderResult: geocoder result
        """
        x = response["geometry"]["coordinates"][0]
        y = response["geometry"]["coordinates"][1]

        properties = response.get("properties")
        label = properties.get("name", "")
        groupe = properties.get("type", "")

        if groupe == "house":
            # add house number to label
            label += " " + properties.get("housenumber", "")
            # add street to label
            label += " " + properties.get("street", "")

        if groupe in ["house", "street"]:
            # add city to label
            label += " " + properties.get("city", "")

        if groupe in ["house", "street", "city"]:
            # add city code to label
            label += " " + properties.get("postcode", "")

        geom = QgsGeometry.fromPointXY(QgsPointXY(x, y))
        crs = QgsCoordinateReferenceSystem("EPSG:4326")
        res = QgsGeocoderResult(
            label,
            geom,
            crs,
        )
        attributes = {}
        for attribute, _ in self._attributes.items():
            attributes[attribute] = properties.get(attribute, None)

        if "extent" in properties:
            extent = properties["extent"]
            if len(extent) == 4:
                res.setViewport(
                    QgsRectangle(extent[0], extent[1], extent[2], extent[3])
                )
        else:
            width = self._width_from_type(groupe)
            res.setViewport(
                self.create_rectangle_around_point(crs, QgsPointXY(x, y), width, width)
            )
        res.setGroup(groupe)
        res.setAdditionalAttributes(attributes)
        return res

    def _width_from_type(self, type_adress: str) -> int:
        """Get extent width in meter for type of adress

        :param type_adress: type of adress
        :type type_adress: str
        :return: extent with in meter
        :rtype: int
        """
        # zoom policy has we don't have extent in the results
        scale = 25000

        if type_adress == "house":
            scale = 2000
        elif type_adress == "street":
            scale = 5000
        elif type_adress == "locality":
            scale = 5000

        return scale
