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


class FrenchBanGeocoder(RestAPIGeocoder):
    """Geocoder for french BAN API"""

    _last_request_timestamp: int = 0

    def __init__(self):
        super().__init__()
        self.max_request_per_second = 50

    def set_last_request_timestamp(self, timestamp: int) -> int:
        """Define timestamp for last request

        :param timestamp: request timestamp
        :type timestamp: int
        """
        FrenchBanGeocoder._last_request_timestamp = timestamp

    def last_request_timestamp(self) -> int:
        """Get last request timestamp

        :return: last request timestamp
        :rtype: int
        """
        return FrenchBanGeocoder._last_request_timestamp

    @property
    def _attributes(self) -> List[str]:
        """Get attributes to read from french BAN API properties

        Returns:
            List[str]: attributes
        """
        return [
            "id",
            "type",
            "name",
            "postcode",
            "citycode",
            "city",
            "district",
            "housenumber",
            "street",
            "population",
            "context",
            "municipality",
            "oldcitycode",
            "oldcity",
            "label",
            "x",
            "y",
            "importance",
        ]

    def request_url(self, reverse: bool = False) -> str:
        """Define request url

        :param reverse: True for reverse geocoding, False otherwise, defaults to False
        :type reverse: bool, optional
        :raises NotImplementedError: method not implemented in derived class
        :return: request url for geocoding
        :rtype: str
        """
        url_service = self.plg_settings.gpf_url
        if reverse:
            return f"{url_service}reverse"
        return f"{url_service}search"

    @property
    def request_url_query(self):
        """Define default request url query

        Returns:
            str: request url query
        """
        return self.plg_settings.request_url_query

    def maximum_result_for_inverse_geocoding(self) -> int:
        """Maximum result for an inverse geocoding

        :return: maximum result
        :rtype: int
        """
        return 50

    def get_reverse_geocode_query(self, feature: QgsFeature) -> Optional[str]:
        """Get query for reverse geocode
        For point we use &lon&lat
        For polygon we searchgeom associated with centroid
        For all other geometry type centroid is use as point

        :param feature: input feature
        :type feature: QgsFeature
        :return: reverse geocode query, None is feature geometry is None
        :rtype: Optional[str]
        """
        geometry = feature.geometry()
        if geometry:
            center = geometry.centroid().asPoint()
            if geometry.type() == Qgis.GeometryType.Point:
                point = geometry.asPoint()
                query = f"&lon={point.x()}&lat={point.y()}"
            elif geometry.type() == Qgis.GeometryType.Polygon:
                query = (
                    f"searchgeom={geometry.asJson()}&lon={center.x()}&lat={center.y()}"
                )
            else:
                query = f"&lon={center.x()}&lat={center.y()}"
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
        label = properties.get("label")
        groupe = properties.get("type")

        if groupe == "municipality":
            # add city code to label
            label += " " + properties.get("citycode")

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

        # Define viewport from extent or define default from type
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

        if type_adress == "housenumber":
            scale = 2000
        elif type_adress == "street":
            scale = 5000
        elif type_adress == "locality":
            scale = 5000

        return scale
