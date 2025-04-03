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


class PhotonGeocoder(RestAPIGeocoder):
    """Geocoder for Photon API"""

    def __init__(self):
        super().__init__()

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
            "countycode",
            "osm_key",
            "osm_value",
            "osm_type",
        ]

    @property
    def request_url(self) -> str:
        """Define request url

        Returns:
            str: request url
        """
        return self.plg_settings.request_photon_url

    @property
    def request_url_query(self):
        """Define default request url query

        Returns:
            str: request url query
        """
        return self.plg_settings.request_photon_url_query

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
        label = properties.get("name")
        groupe = properties.get("type")

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
            if attribute in properties:
                attributes[attribute] = properties[attribute]

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
