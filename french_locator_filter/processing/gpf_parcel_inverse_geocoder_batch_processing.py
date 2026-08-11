from french_locator_filter.core.geocoder.gpf_parcel_geocoder import GpfParcelGeocoder
from french_locator_filter.processing.inverse_geocoder_batch_processing import (
    InverseGeocoderBatchProcessing,
)
from french_locator_filter.processing.utils import get_short_string, get_user_manual_url

geocoder = GpfParcelGeocoder()


class GpfParcelInverseGeocoderBatchProcessing(InverseGeocoderBatchProcessing):
    def __init__(self):
        super().__init__(geocoder)

    def displayName(self):
        return self.tr("Géocodage inversé de parcelle avec la Géoplateforme")

    def helpUrl(self):
        return get_user_manual_url(self.name())

    def shortHelpString(self):
        return get_short_string(self.name(), self.displayName())

    def name(self):
        return "gpf_parcel_inverse_geocoder_batch"

    def group(self):
        return ""

    def groupId(self):
        return ""

    def createInstance(self):
        return GpfParcelInverseGeocoderBatchProcessing()

    def tags(self):
        return ["inverse geocode", "géoplateforme", "parcelle", "cadastre", "batch"]
