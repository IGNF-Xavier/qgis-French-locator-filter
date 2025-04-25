# standard library
from typing import List

# PyQGIS
from qgis.core import (
    QgsCoordinateReferenceSystem,
    QgsGeocoderResult,
    QgsGeometry,
    QgsPointXY,
    QgsRectangle,
)

# project
from french_locator_filter.core.geocoder.rest_api_geocoder import RestAPIGeocoder


class FrenchBanGeocoder(RestAPIGeocoder):
    """Geocoder for french BAN API"""

    def __init__(self):
        super().__init__()

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

    @property
    def request_url(self) -> str:
        """Define request url

        Returns:
            str: request url
        """
        return self.plg_settings.request_url

    @property
    def request_url_query(self):
        """Define default request url query

        Returns:
            str: request url query
        """
        return self.plg_settings.request_url_query

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
            if attribute in properties:
                attributes[attribute] = properties[attribute]

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
