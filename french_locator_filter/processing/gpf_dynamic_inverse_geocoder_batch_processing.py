from french_locator_filter.core.geocoder.gpf_dynamic_geocoder import GpfDynamicGeocoder
from french_locator_filter.processing.inverse_geocoder_batch_processing import (
    InverseGeocoderBatchProcessing,
)
from french_locator_filter.processing.utils import get_short_string, get_user_manual_url

geocoder = GpfDynamicGeocoder()


class GpfDynamicInverseGeocoderBatchProcessing(InverseGeocoderBatchProcessing):
    def __init__(self):
        super().__init__(geocoder)

    def displayName(self):
        return self.tr("Géocodage inversé Géoplateforme (index configurables)")

    def helpUrl(self):
        return get_user_manual_url(self.name())

    def shortHelpString(self):
        return get_short_string(self.name(), self.displayName())

    def name(self):
        return "gpf_dynamic_inverse_geocoder_batch"

    def group(self):
        return ""

    def groupId(self):
        return ""

    def createInstance(self):
        return GpfDynamicInverseGeocoderBatchProcessing()

    def tags(self):
        return ["inverse geocode", "géoplateforme", "index", "poi", "batch"]
