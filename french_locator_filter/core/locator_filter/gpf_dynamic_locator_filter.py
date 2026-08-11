#! python3  # noqa: E265

"""
Locator Filter.
"""

# PyQGIS
from qgis.core import QgsGeocoderInterface, QgsLocatorFilter

# project
from french_locator_filter.core.geocoder.gpf_dynamic_geocoder import GpfDynamicGeocoder
from french_locator_filter.core.locator_filter.rest_api_locator_filter import (
    RestAPILocatorFilter,
)

# ############################################################################
# ########## Classes ###############
# ##################################


class GpfDynamicGeocoderLocatorFilter(RestAPILocatorFilter):
    """QGIS Locator Filter subclass using the Géoplateforme API with a
    user-configurable set of indexes (address, poi, parcel, ...)"""

    def _create_geocoder(self) -> QgsGeocoderInterface:
        """Create QgsGeocoderInterface used to fetch result

        :return: geocoder interface
        :rtype: QgsGeocoderInterface
        """
        return GpfDynamicGeocoder()

    def name(self) -> str:
        """Returns the unique name for the filter. This should be an untranslated \
        string identifying the filter.

        :return: filter unique name
        :rtype: str
        """
        return self.__class__.__name__

    def clone(self) -> QgsLocatorFilter:
        """Creates a clone of the filter. New requests are always executed in a clone \
        of the original filter.

        :return: clone of the actual filter
        :rtype: QgsLocatorFilter
        """
        return GpfDynamicGeocoderLocatorFilter(self._canvas)

    def displayName(self) -> str:
        """Returns a translated, user-friendly name for the filter.

        :return: user-friendly name to be displayed
        :rtype: str
        """
        return self.tr("Géoplateforme (index configurables)")

    def prefix(self) -> str:
        """Returns the search prefix character(s) for this filter. Prefix a search with \
        these characters will restrict the locator search to only include results from \
        this filter.

        :return: search prefix for the filter
        :rtype: str
        """
        return "gpf"
