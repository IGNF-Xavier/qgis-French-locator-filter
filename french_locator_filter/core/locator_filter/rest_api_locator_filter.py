#! python3  # noqa: E265

"""
Locator Filter.
"""

# standard library
import json

# PyQGIS
from qgis.core import (
    Qgis,
    QgsFeedback,
    QgsLocatorContext,
    QgsLocatorFilter,
    QgsLocatorResult,
)
from qgis.gui import QgisInterface
from qgis.PyQt.QtWidgets import QWidget
from qgis.utils import iface

# project
from french_locator_filter.__about__ import __title__
from french_locator_filter.toolbelt import (
    NetworkRequestsManager,
    PlgLogger,
    PlgOptionsManager,
)

# ############################################################################
# ########## Classes ###############
# ##################################


class RestAPILocatorFilter(QgsLocatorFilter):
    """Abstract class for QgsLocatorFilter from a REST API

    Must implement at least these method:
    - process_json_response
    - trigger_result_from_json_response

    :param iface: An interface instance that will be passed to this class which \
    provides the hook by which you can manipulate the QGIS application at run time.
    :type iface: QgisInterface
    """

    def __init__(self, iface: QgisInterface = iface):
        self.iface = iface
        self.log = PlgLogger().log
        self.plg_settings = PlgOptionsManager.get_plg_settings()

        super(QgsLocatorFilter, self).__init__()

    def hasConfigWidget(self) -> bool:
        """Should return True if the filter has a configuration widget.

        :return: configuration widget available
        :rtype: bool
        """
        return True

    def openConfigWidget(self, parent: QWidget = None):
        """Opens the configuration widget for the filter (if it has one), with the \
        specified parent widget. self.hasConfigWidget() must return True.

        :param parent: prent widget, defaults to None
        :type parent: QWidget, optional
        """
        self.iface.showOptionsDialog(
            parent=parent, currentPage=f"mOptionsPage{__title__}"
        )

    def check_search(self, search: str) -> bool:
        """Check search from current configuration

        :param search: search value
        :type search: str
        :return: True if search is valid, False otherwise
        :rtype: bool
        """
        # ignore if search terms is inferior than minimum number of chars
        if len(search) < self.plg_settings.min_search_length:
            self.log(
                message=self.tr("API search not triggered. Reason: ")
                + self.tr(
                    "minimum chars {} not reached: {}".format(
                        self.plg_settings.min_search_length, len(search)
                    )
                ),
                log_level=Qgis.MessageLevel.NoLevel,
            )
            return False

        # ignore if search terms is equal to the prefix
        if search.rstrip() == self.prefix:
            self.log(
                message=self.tr("API search not triggered. Reason: ")
                + self.tr("search term is matching the prefix."),
                log_level=Qgis.MessageLevel.NoLevel,
            )
            return False

        return True

    def process_json_response(self, response: dict) -> None:
        """Process json response from REST API.
        QgsLocatorResult sent MUST have a dict in userData

        Args:
            response (dict): json response

        Raises:
            NotImplementedError: method not implemented in derived class
        """
        raise NotImplementedError(
            "process_json_response must be implemented in RestAPILocatorFilter derived classes"
        )

    @property
    def request_url(self) -> str:
        """Define request url

        Raises:
            NotImplementedError: method not implemented in derived class

        Returns:
            str: request url
        """
        raise NotImplementedError(
            "request_url must be implemented in RestAPILocatorFilter derived classes"
        )

    @property
    def request_url_query(self):
        """Define default request url query

        Returns:
            str: request url query
        """
        raise NotImplementedError(
            "request_url_query must be implemented in RestAPILocatorFilter derived classes"
        )

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

        :param search: text entered by the end-user into the locator line edit
        :type search: str
        :param context: [description]
        :type context: QgsLocatorContext
        :param feedback: [description]
        :type feedback: QgsFeedback
        """
        if not self.check_search(search):
            return

        # request
        try:
            qntwk = NetworkRequestsManager()
            qurl = qntwk.build_url(
                request_url=self.request_url,
                request_url_query=self.request_url_query,
                additional_query=f"&q={search}",
            )
            response_content = qntwk.get_url(url=qurl)
        except Exception as err:
            self.log(message=err, log_level=1)
            return

        # process response
        try:
            # load response as a dict
            response = json.loads(str(response_content, "UTF8"))
            # process json response
            self.process_json_response(response)
        except Exception as exc:
            self.log(message=f"Response processing failed. : {exc}", log_level=1)
            return

    def trigger_result_from_json_response(self, response: dict) -> None:
        """Trigger locator result with json response from REST API

        Args:
            response (dict): json response

        Raises:
            NotImplementedError: method not implemented in derived class
        """
        raise NotImplementedError(
            "trigger_result_from_json_response must be implemented in RestAPILocatorFilter derived classes"
        )

    def triggerResult(self, result: QgsLocatorResult) -> None:
        """Triggers a filter result from this filter. This is called when one of the \
        results obtained by a call to fetchResults() is triggered by a user. \
        The filter subclass must implement logic here to perform the desired operation \
        for the search result. E.g. a file search filter would open file associated \
        with the triggered result.

        :param result: result selected by user
        :type result: QgsLocatorResult
        """
        # Newer Version of PyQT does not expose the .userData (Leading to core dump)
        # Try via get Function, otherwise access attribute
        # Since 3.38, it changed again for a _userData() method.
        # See: https://github.com/qgis/QGIS/pull/56550
        try:
            doc = result._userData()
            self.log(
                message=self.tr(
                    "Result triggerred by the user received: {}".format(
                        doc.get("properties").get("label")
                    )
                ),
                log_level=Qgis.MessageLevel.NoLevel,
            )
        except Exception as err:
            # fallback to former method getUserData() just in case
            doc = result.getUserData()
            self.log(
                message=self.tr(
                    "Something went wrong during result deserialization: {}. "
                    "Trying another method...".format(err)
                ),
                log_level=Qgis.MessageLevel.Warning,
            )

        self.trigger_result_from_json_response(doc)
