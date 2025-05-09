from french_locator_filter.core.geocoder.photon_geocoder import PhotonGeocoder
from french_locator_filter.processing.inverse_geocoder_batch_processing import (
    InverseGeocoderBatchProcessing,
)

photon_geocoder = PhotonGeocoder()


class PhotonInverseGeocoderBatchProcessing(InverseGeocoderBatchProcessing):
    def __init__(self):
        super().__init__(photon_geocoder)

    def displayName(self):
        return self.tr("Géocodage inversé avec Photon")

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
