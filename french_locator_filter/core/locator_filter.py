#! python3  # noqa: E265

"""
    Main plugin module.
"""

# standard library
import json
import logging

# PyQGIS
from qgis.core import (
    QgsCoordinateReferenceSystem,
    QgsCoordinateTransform,
    QgsFeedback,
    QgsLocatorContext,
    QgsLocatorFilter,
    QgsLocatorResult,
    QgsPointXY,
    QgsProject,
)
from qgis.PyQt.QtCore import pyqtSignal

from french_locator_filter.toolbelt import PlgLogger, PlgOptionsManager

# project
from french_locator_filter.toolbelt.networkaccessmanager import (
    NetworkAccessManager,
    RequestsException,
)

# ############################################################################
# ########## Globals ###############
# ##################################

logger = logging.getLogger(__name__)

# ############################################################################
# ########## Classes ###############
# ##################################


class FrenchBanGeocoderLocatorFilter(QgsLocatorFilter):

    USER_AGENT = b"Mozilla/5.0 QGIS LocatorFilter"

    SEARCH_URL = "https://api-adresse.data.gouv.fr/search/?limit=10&autocomplete=1&q="

    resultProblem = pyqtSignal(str)

    def __init__(self, iface):
        self.iface = iface
        self.log = PlgLogger().log

        super(QgsLocatorFilter, self).__init__()

    def name(self):
        return self.__class__.__name__

    def clone(self):
        return FrenchBanGeocoderLocatorFilter(self.iface)

    def displayName(self):
        return "Géocodeur API Adresse FR"

    def prefix(self):
        return "fra"

    def fetchResults(
        self, search: str, context: QgsLocatorContext, feedback: QgsFeedback
    ):
        """Retrieves the filter results for a specified search string. The context \
        argument encapsulates the context relating to the search (such as a map extent \
        to prioritize). \

        Implementations of fetchResults() should emit the resultFetched() signal \
        whenever they encounter a matching result. \
        Subclasses should periodically check the feedback object to determine whether \
        the query has been canceled. If so, the subclass should return from this method \
        as soon as possible. This will be called from a background thread unless \
        flags() returns the QgsLocatorFilter.FlagFast flag.

        :param search: [description]
        :type search: str
        :param context: [description]
        :type context: QgsLocatorContext
        :param feedback: [description]
        :type feedback: QgsFeedback
        """

        if len(search) < 2:
            return

        # build URL
        url = "{}{}".format(self.SEARCH_URL, search)
        if __debug__:
            self.log(f"Search url {url}")

        # request
        nam = NetworkAccessManager()
        try:

            headers = {b"User-Agent": self.USER_AGENT}
            # use BLOCKING request, as fetchResults already has it's own thread!
            (response, content) = nam.request(url, headers=headers, blocking=True)

            if (
                response.status_code == 200
            ):  # other codes are handled by NetworkAccessManager
                content_string = content.decode("utf-8")
                locations = json.loads(content_string)

                # loop on features in json collection
                for loc in locations["features"]:

                    result = QgsLocatorResult()
                    result.filter = self
                    label = loc["properties"]["label"]
                    if loc["properties"]["type"] == "municipality":
                        # add city code to label
                        label += " " + loc["properties"]["citycode"]
                    result.displayString = label
                    result.group = loc["properties"]["type"]
                    # use the json full item as userData, so all info is in it:
                    result.userData = loc
                    self.resultFetched.emit(result)

        except RequestsException as err:
            self.log(message=err, log_level=1, push=True)

    def triggerResult(self, result: QgsLocatorResult):
        """Triggers a filter result from this filter. This is called when one of the \
        results obtained by a call to fetchResults() is triggered by a user. \
        The filter subclass must implement logic here to perform the desired operation \
        for the search result. E.g. a file search filter would open file associated \
        with the triggered result.

        :param result: [description]
        :type result: QgsLocatorResult
        """
        if __debug__:
            self.log(
                message=f"DEBUG - Selected address: {result.displayString}", log_level=4
            )
        doc = result.userData
        x = doc["geometry"]["coordinates"][0]
        y = doc["geometry"]["coordinates"][1]

        centerPoint = QgsPointXY(x, y)

        dest_crs = QgsProject.instance().crs()
        results_crs = QgsCoordinateReferenceSystem(
            4326, QgsCoordinateReferenceSystem.PostgisCrsId
        )
        aTransform = QgsCoordinateTransform(
            results_crs, dest_crs, QgsProject.instance()
        )
        centerPointProjected = aTransform.transform(centerPoint)
        aTransform.transform(centerPoint)

        # centers to adress coordinates
        self.iface.mapCanvas().setCenter(centerPointProjected)

        # zoom policy has we don't have extent in the results
        scale = 25000

        type_adress = doc["properties"]["type"]

        if type_adress == "housenumber":
            scale = 2000
        elif type_adress == "street":
            scale = 5000
        elif type_adress == "locality":
            scale = 5000

        # finally zoom actually
        self.iface.mapCanvas().zoomScale(scale)
        self.iface.mapCanvas().refresh()
