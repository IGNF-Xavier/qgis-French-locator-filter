# standard library
from typing import List, Optional

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
    def _attributes(self) -> List[str]:
        """Get attributes to read from Photon API properties

        Returns:
            List[str]: attributes
        """
        return [
            "name",
            "street",
            "housenumber",
            "postcode",
            "state",
            "country",
            "countrycode",
            "osm_id",
            "osm_key",
            "osm_value",
            "osm_type",
            "city",
            "locality",
            "county",
            "type",
            "district",
        ]

    def request_url(self, reverse: bool = False) -> str:
        """Define request url

        :param reverse: True for reverse geocoding, False otherwise, defaults to False
        :type reverse: bool, optional
        :raises NotImplementedError: method not implemented in derived class
        :return: request url for geocoding
        :rtype: str
        """
        if reverse:
            return f"{self.plg_settings.request_photon_url}/reverse"
        return f"{self.plg_settings.request_photon_url}/api/"

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
        for attribute in self._attributes:
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
