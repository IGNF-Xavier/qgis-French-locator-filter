# standard library

# project
from french_locator_filter.core.geocoder.rest_api_geocoder import RestAPIGeocoder


class GpfRestApiGeocoder(RestAPIGeocoder):
    """Abstract class for geocoders hitting the Géoplateforme geocodage host
    (data.geopf.fr). Shares a single class-level rate-limit counter across all
    subclasses so the documented 50 req/s per IP limit is respected even when
    several geocoders (address, parcel, ...) hit the host concurrently."""

    _last_request_timestamp: int = 0

    def __init__(self):
        super().__init__()
        self.max_request_per_second = 50

    def set_last_request_timestamp(self, timestamp: int) -> None:
        """Define timestamp for last request

        :param timestamp: request timestamp
        :type timestamp: int
        """
        GpfRestApiGeocoder._last_request_timestamp = timestamp

    def last_request_timestamp(self) -> int:
        """Get last request timestamp

        :return: last request timestamp
        :rtype: int
        """
        return GpfRestApiGeocoder._last_request_timestamp
