#! python3  # noqa: E265

"""
    Locator Filter.
"""

# PyQGIS
from qgis.core import (
    QgsCoordinateReferenceSystem,
    QgsCoordinateTransform,
    QgsLocatorFilter,
    QgsLocatorResult,
    QgsPointXY,
    QgsProject,
)
from qgis.gui import QgisInterface
from qgis.utils import iface

# project
from french_locator_filter.core.rest_api_locator_filter import RestAPILocatorFilter
from french_locator_filter.toolbelt import PlgLogger, PlgOptionsManager

# ############################################################################
# ########## Classes ###############
# ##################################


class FrenchBanGeocoderLocatorFilter(RestAPILocatorFilter):
    """QGIS Locator Filter subclass.

    :param iface: An interface instance that will be passed to this class which \
    provides the hook by which you can manipulate the QGIS application at run time.
    :type iface: QgisInterface
    """

    def __init__(self, iface: QgisInterface = iface):
        self.iface = iface
        self.log = PlgLogger().log
        self.plg_settings = PlgOptionsManager.get_plg_settings()

        super(RestAPILocatorFilter, self).__init__(iface)

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
        return FrenchBanGeocoderLocatorFilter(iface)

    def displayName(self) -> str:
        """Returns a translated, user-friendly name for the filter.

        :return: user-friendly name to be displayed
        :rtype: str
        """
        return self.tr("French Adress geocoder")

    def prefix(self) -> str:
        """Returns the search prefix character(s) for this filter. Prefix a search with \
        these characters will restrict the locator search to only include results from \
        this filter.

        :return: search prefix for the filter
        :rtype: str
        """
        return "fra"

    @property
    def request_url(self) -> str:
        """Define request url

        Returns:
            str: request url
        """
        return self.plg_settings.request_url

    @property
    def request_url_query(self):
        """Define default request url query

        Returns:
            str: request url query
        """
        return self.plg_settings.request_url_query

    def process_json_response(self, response: dict) -> None:
        """Process json response from REST API

        Args:
            response (dict): json response
        """
        # loop on features in json collection
        for loc in response.get("features"):
            result = QgsLocatorResult()
            result.filter = self
            label = loc.get("properties").get("label")
            if loc.get("properties").get("type") == "municipality":
                # add city code to label
                label += " " + loc.get("properties").get("citycode")
            result.displayString = label
            result.group = loc.get("properties").get("type")

            # use the json full item as userData, so all info is in it:
            result.userData = loc
            self.resultFetched.emit(result)

    def trigger_result_from_json_response(self, response: dict) -> None:
        """Trigger locator result with json response from REST API

        Args:
            response (dict): json response
        """
        x = response["geometry"]["coordinates"][0]
        y = response["geometry"]["coordinates"][1]

        centerPoint = QgsPointXY(x, y)
        dest_crs = QgsProject.instance().crs()
        results_crs = QgsCoordinateReferenceSystem.fromEpsgId(4326)
        coords_transform = QgsCoordinateTransform(
            results_crs, dest_crs, QgsProject.instance()
        )
        centerPointProjected = coords_transform.transform(centerPoint)
        coords_transform.transform(centerPoint)

        # centers to adress coordinates
        iface.mapCanvas().setCenter(centerPointProjected)

        # zoom policy has we don't have extent in the results
        scale = 25000

        type_adress = response.get("properties").get("type")

        if type_adress == "housenumber":
            scale = 2000
        elif type_adress == "street":
            scale = 5000
        elif type_adress == "locality":
            scale = 5000

        # finally zoom actually
        iface.mapCanvas().zoomScale(scale)
        iface.mapCanvas().refresh()
