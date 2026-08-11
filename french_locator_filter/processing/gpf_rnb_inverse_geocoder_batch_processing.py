from french_locator_filter.core.geocoder.gpf_rnb_geocoder import GpfRnbGeocoder
from french_locator_filter.processing.inverse_geocoder_batch_processing import (
    InverseGeocoderBatchProcessing,
)
from french_locator_filter.processing.utils import get_short_string, get_user_manual_url

geocoder = GpfRnbGeocoder()


class GpfRnbInverseGeocoderBatchProcessing(InverseGeocoderBatchProcessing):
    def __init__(self):
        super().__init__(geocoder)

    def displayName(self):
        return self.tr("Géocodage inversé RNB (bâtiment)")

    def helpUrl(self):
        return get_user_manual_url(self.name())

    def shortHelpString(self):
        return get_short_string(self.name(), self.displayName())

    def name(self):
        return "gpf_rnb_inverse_geocoder_batch"

    def group(self):
        return ""

    def groupId(self):
        return ""

    def createInstance(self):
        return GpfRnbInverseGeocoderBatchProcessing()

    def tags(self):
        return ["inverse geocode", "rnb", "bâtiment", "batch"]
