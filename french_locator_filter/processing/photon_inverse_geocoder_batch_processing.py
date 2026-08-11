from french_locator_filter.core.geocoder.photon_geocoder import PhotonGeocoder
from french_locator_filter.processing.inverse_geocoder_batch_processing import (
    InverseGeocoderBatchProcessing,
)
from french_locator_filter.processing.utils import get_short_string, get_user_manual_url

photon_geocoder = PhotonGeocoder()


class PhotonInverseGeocoderBatchProcessing(InverseGeocoderBatchProcessing):
    def __init__(self):
        super().__init__(photon_geocoder)

    def displayName(self):
        return self.tr("Géocodage inversé avec Photon")

    def helpUrl(self):
        return get_user_manual_url(self.name())

    def shortHelpString(self):
        return get_short_string(self.name(), self.displayName())

    def name(self):
        return "photon_inverse_geocoder_batch"

    def group(self):
        return ""

    def groupId(self):
        return ""

    def createInstance(self):
        return PhotonInverseGeocoderBatchProcessing()

    def tags(self):
        return ["inverse geocode", "photon", "batch"]
