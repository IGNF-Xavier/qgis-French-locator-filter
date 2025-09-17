# standard library
import json
import time
from typing import List, Optional

# PyQGIS
from qgis.core import (
    Qgis,
    QgsCoordinateReferenceSystem,
    QgsCoordinateTransform,
    QgsFeature,
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
from qgis.PyQt.QtCore import QCoreApplication, QDateTime, QMetaType

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

    def tr(self, message: str) -> str:
        """Get the translation for a string using Qt translation API.

        :param message: string to be translated.
        :type message: str

        :returns: Translated version of message.
        :rtype: str
        """
        return QCoreApplication.translate(self.__class__.__name__, message)

    def flags(self) -> QgsGeocoderInterface.Flags:
        """Returns the geocoder's capability flags.

        Returns:
            QgsGeocoderInterface.Flags: flags
        """
        return (
            QgsGeocoderInterface.Flag.GeocodesStrings
            | QgsGeocoderInterface.Flag.GeocodesFeatures
        )

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
            fields.append(QgsField(attribute, QMetaType.Type.QString))

        return fields

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

    def request_url(self, reverse: bool = False) -> str:
        """Define request url

        :param reverse: True for reverse geocoding, False otherwise, defaults to False
        :type reverse: bool, optional
        :raises NotImplementedError: method not implemented in derived class
        :return: request url for geocoding
        :rtype: str
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

    def set_last_request_timestamp(self, timestamp: int) -> None:
        """Define timestamp for last request

        :param timestamp: request timestamp
        :type timestamp: int
        :raises NotImplementedError: method not implemented in derived class
        """
        raise NotImplementedError(
            "set_last_request_timestamp must be implemented in RestAPIGeocoder derived classes"
        )

    def last_request_timestamp(self) -> int:
        """Get last request timestamp

        :raises NotImplementedError: method not implemented in derived class
        :return: last request timestamp
        :rtype: int
        """
        raise NotImplementedError(
            "last_request_timestamp must be implemented in RestAPIGeocoder derived classes"
        )

    def get_reverse_geocode_query(self, feature: QgsFeature) -> Optional[str]:
        """Get query for reverse geocode

        :param feature: input feature
        :type feature: QgsFeature
        :raises NotImplementedError: method not implemented in derived class
        :return: reverse geocode query
        :rtype: Optional[str]
        """
        raise NotImplementedError(
            "get_reverse_geocode_query must be implemented in RestAPIGeocoder derived classes"
        )

    def maximum_result_for_inverse_geocoding(self) -> int:
        """Maximum result for an inverse geocoding

        :return: maximum result
        :rtype: int
        """
        return 1

    def geocodeFeature(
        self,
        feature: QgsFeature,
        context: QgsGeocoderContext,
        feedback: Optional[QgsFeedback] = None,
    ) -> List[QgsGeocoderResult]:
        """Geocode a feature

        :param feature: input feature
        :type feature: QgsFeature
        :param context: geocoder context
        :type context: QgsGeocoderContext
        :param feedback: feedback, defaults to None
        :type feedback: Optional[QgsFeedback], optional
        :return: list of result for feature
        :rtype: List[QgsGeocoderResult]
        """

        # Limit number of request per second
        while (
            QDateTime.currentMSecsSinceEpoch() - self.last_request_timestamp()
            < 1000 / self.max_request_per_second
        ):
            time.sleep(0.05)
            if feedback and feedback.isCanceled():
                return []

        query = self.get_reverse_geocode_query(feature)
        if query:
            # request
            try:
                qntwk = NetworkRequestsManager()
                qurl = qntwk.build_url(
                    request_url=self.request_url(reverse=True),
                    request_url_query=query,
                )
                response_content = qntwk.get_url(url=qurl)
                # load response as a dict
                responses = json.loads(str(response_content, "UTF8"))
                return [
                    self._result_from_json(response)
                    for response in responses.get("features")
                ]
            except Exception as err:
                self.log(
                    message=self.tr(
                        "Erreur lors de la demande de géocodage inversé : {}".format(
                            err
                        )
                    ),
                    log_level=1,
                )
                return []
            finally:
                self.set_last_request_timestamp(QDateTime.currentMSecsSinceEpoch())
        return []

    def geocodeString(
        self,
        string: str,
        context: QgsGeocoderContext,
        feedback: Optional[QgsFeedback] = None,
    ) -> List[QgsGeocoderResult]:
        """Geocode string with a REST API. Result are defined with _result_from_json method.

        Args:
            string (str): search string
            context (QgsGeocoderContext): geocoding context
            feedback (QgsFeedback | None, optional): feedback for geocoding. Defaults to None

        Returns:
            List[QgsGeocoderResult]: list of geocoding results
        """

        # TODO : for now to bounding box from context and feedback

        # Limit number of request per second
        while (
            QDateTime.currentMSecsSinceEpoch() - self.last_request_timestamp()
            < 1000 / self.max_request_per_second
        ):
            time.sleep(0.05)
            if feedback and feedback.isCanceled():
                return []
        # request
        try:
            qntwk = NetworkRequestsManager()
            qurl = qntwk.build_url(
                request_url=self.request_url(reverse=False),
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
            self.log(
                message=self.tr(
                    "Erreur lors de la demande de géocodage : {}".format(err)
                ),
                log_level=1,
            )
            return []
        finally:
            self.set_last_request_timestamp(QDateTime.currentMSecsSinceEpoch())

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
