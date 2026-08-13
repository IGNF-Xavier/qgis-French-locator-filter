from french_locator_filter.core.geocoder.gpf_chained_geocoder import GpfChainedGeocoder
from french_locator_filter.processing.inverse_geocoder_batch_processing import (
    InverseGeocoderBatchProcessing,
)
from french_locator_filter.processing.utils import get_short_string, get_user_manual_url

geocoder = GpfChainedGeocoder()


class GpfChainedInverseGeocoderBatchProcessing(InverseGeocoderBatchProcessing):
    def __init__(self):
        super().__init__(geocoder)

    def displayName(self):
        return self.tr("Géocodage inversé fiche complète (bâtiment + parcelle)")

    def helpUrl(self):
        return get_user_manual_url(self.name())

    def shortHelpString(self):
        return get_short_string(self.name(), self.displayName())

    def name(self):
        return "gpf_chained_inverse_geocoder_batch"

    def group(self):
        return ""

    def groupId(self):
        return ""

    def createInstance(self):
        return GpfChainedInverseGeocoderBatchProcessing()

    def tags(self):
        return ["inverse geocode", "géoplateforme", "rnb", "parcelle", "chainage", "batch"]
