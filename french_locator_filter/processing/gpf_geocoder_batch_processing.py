from qgis.analysis import QgsBatchGeocodeAlgorithm
from qgis.core import QgsCoordinateReferenceSystem
from qgis.PyQt.QtCore import QCoreApplication

from french_locator_filter.core.geocoder.addok_ban_fr_geocoder import FrenchBanGeocoder

geocoder = FrenchBanGeocoder()


class GpfGeocoderBatchProcessing(QgsBatchGeocodeAlgorithm):
    def __init__(self):
        super().__init__(geocoder)

    def displayName(self):
        return self.tr("Batch Géoplateforme geocoding")

    def name(self):
        return "gpf_geocoder_batch"

    def group(self):
        return ""

    def groupId(self):
        return ""

    def createInstance(self):
        return GpfGeocoderBatchProcessing()

    def tr(self, message: str) -> str:
        """Get the translation for a string using Qt translation API.

        :param message: string to be translated.
        :type message: str

        :returns: Translated version of message.
        :rtype: str
        """
        return QCoreApplication.translate(self.__class__.__name__, message)

    def outputCrs(
        self, input_crs: QgsCoordinateReferenceSystem
    ) -> QgsCoordinateReferenceSystem:
        use_crs = QgsCoordinateReferenceSystem("EPSG:4326")
        if input_crs.isValid():
            use_crs = input_crs
        return super().outputCrs(use_crs)

    def tags(self):
        return ["geocode", "géoplateforme", "batch"]
