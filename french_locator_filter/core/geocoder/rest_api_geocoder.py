# standard library
import json
from typing import List, Optional

# PyQGIS
from qgis.core import (
    Qgis,
    QgsCoordinateReferenceSystem,
    QgsCoordinateTransform,
    QgsFeedback,
    QgsField,
    QgsFields,
    QgsGeocoderContext,
    QgsGeocoderInterface,
    QgsGeocoderResult,
    QgsPointXY,
    QgsProject,
    QgsRectangle,
)

# project
from french_locator_filter.toolbelt.log_handler import PlgLogger
from french_locator_filter.toolbelt.network_manager import NetworkRequestsManager
from french_locator_filter.toolbelt.preferences import PlgOptionsManager


class RestAPIGeocoder(QgsGeocoderInterface):
    """Abstract class for QgsGeocoderInterface from a REST API"""

    def __init__(self):
        self.log = PlgLogger().log
        self.plg_settings = PlgOptionsManager.get_plg_settings()
        super(QgsGeocoderInterface, self).__init__()

    def flags(self) -> QgsGeocoderInterface.Flags:
        """Returns the geocoder's capability flags.

        Returns:
            QgsGeocoderInterface.Flags: flags
        """
        return QgsGeocoderInterface.Flag.GeocodesStrings

    @property
    def _attributes(self) -> List[str]:
        """Get attributes to read from REST API properties.
        To be overriden in implementation, empty list by default

        Returns:
            List[str]: attributes
        """
        return []

    def appendedFields(self) -> QgsFields:
        """Returns a set of newly created fields which will be appended to existing features during the geocode operation.
           These fields will include any extra content returned by the geocoder, such as fields for accuracy of the match or correct attribute values.

        Returns:
            QgsFields: appended fields
        """
        fields = QgsFields()
        for attribute in self._attributes:
            fields.append(QgsField(attribute))

        return super().appendedFields()

    def wkbType(self) -> Qgis.WkbType:
        """Returns the WKB type of geometries returned by the geocoder.

        Returns:
            Qgis.WkbType: Qgis.WkbType.Point
        """
        return Qgis.WkbType.Point

    def _result_from_json(self, response: dict) -> QgsGeocoderResult:
        """Create a QgsGeocoderResult from json content

        Args:
            response (dict): json response content

        Returns:
            QgsGeocoderResult: geocoder result
        """
        raise NotImplementedError(
            "_result_from_json must be implemented in RestAPIGeocoder derived classes"
        )

    @property
    def request_url(self) -> str:
        """Define request url

        Raises:
            NotImplementedError: method not implemented in derived class

        Returns:
            str: request url
        """
        raise NotImplementedError(
            "request_url must be implemented in RestAPIGeocoder derived classes"
        )

    @property
    def request_url_query(self):
        """Define default request url query

        Returns:
            str: request url query
        """
        raise NotImplementedError(
            "request_url_query must be implemented in RestAPIGeocoder derived classes"
        )

    def geocodeString(
        self,
        string: str,
        context: QgsGeocoderContext,
        feedback: Optional[QgsFeedback] = None,
    ) -> List[QgsGeocoderResult]:
        """Geocode string with Photon API

        Args:
            string (str): search string
            context (QgsGeocoderContext): geocoding context
            feedback (QgsFeedback | None, optional): feedback for geocoding. Defaults to None

        Returns:
            List[QgsGeocoderResult]: list of geocoding results
        """

        # TODO : for now to bounding box from context and feedback

        # request
        try:
            qntwk = NetworkRequestsManager()
            qurl = qntwk.build_url(
                request_url=self.request_url,
                request_url_query=self.request_url_query,
                additional_query=f"&q={string}",
            )
            response_content = qntwk.get_url(url=qurl)
            # load response as a dict
            responses = json.loads(str(response_content, "UTF8"))
            return [
                self._result_from_json(response)
                for response in responses.get("features")
            ]
        except Exception as err:
            self.log(message=err, log_level=1)
            return []

    def create_rectangle_around_point(
        self,
        crs: QgsCoordinateReferenceSystem,
        center: QgsPointXY,
        width_meters: float,
        height_meters: float,
    ) -> QgsRectangle:
        """Creates a rectangle centered on a QgsPointXY with a width and height in meters,
        taking into account the CRS (supports coordinates in degrees)."""

        # Check if CRS is geographic to create rectange in meter and do conversion
        if crs.isGeographic():
            # Use Web mercator for projection
            crs_projected = QgsCoordinateReferenceSystem("EPSG:3857")
            transform_to_projected = QgsCoordinateTransform(
                crs, crs_projected, QgsProject.instance()
            )

            # Convert center
            center_projected = transform_to_projected.transform(center)

            # Create rectangle with width and height
            rect_projected = QgsRectangle(
                center_projected.x() - width_meters / 2,
                center_projected.y() - height_meters / 2,
                center_projected.x() + width_meters / 2,
                center_projected.y() + height_meters / 2,
            )

            # Convert in degree
            transform_to_geographic = QgsCoordinateTransform(
                crs_projected, crs, QgsProject.instance()
            )

            bottom_left = transform_to_geographic.transform(
                QgsPointXY(rect_projected.xMinimum(), rect_projected.yMinimum())
            )
            top_right = transform_to_geographic.transform(
                QgsPointXY(rect_projected.xMaximum(), rect_projected.yMaximum())
            )

            return QgsRectangle(bottom_left, top_right)
        else:
            # No need for conversion
            return QgsRectangle(
                center.x() - width_meters / 2,
                center.y() - height_meters / 2,
                center.x() + width_meters / 2,
                center.y() + height_meters / 2,
            )
