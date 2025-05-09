from french_locator_filter.core.geocoder.addok_ban_fr_geocoder import FrenchBanGeocoder
from french_locator_filter.processing.inverse_geocoder_batch_processing import (
    InverseGeocoderBatchProcessing,
)

geocoder = FrenchBanGeocoder()


class GpfInverseGeocoderBatchProcessing(InverseGeocoderBatchProcessing):
    def __init__(self):
        super().__init__(geocoder)

    def displayName(self):
        return self.tr("Géocodage inversé avec la Géoplateforme")

    def name(self):
        return "gpf_inverse_geocoder_batch"

    def group(self):
        return ""

    def groupId(self):
        return ""

    def createInstance(self):
        return GpfInverseGeocoderBatchProcessing()

    def tags(self):
        return ["inverse geocode", "géoplateforme", "batch"]
