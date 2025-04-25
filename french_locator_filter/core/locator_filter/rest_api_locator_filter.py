#! python3  # noqa: E265

"""
Locator Filter.
"""

# standard library
from typing import Optional

# PyQGIS
from qgis.core import Qgis, QgsFeedback, QgsLocatorContext
from qgis.gui import QgsGeocoderLocatorFilter, QgsMapCanvas
from qgis.PyQt.QtWidgets import QWidget
from qgis.utils import iface

# project
from french_locator_filter.__about__ import __title__
from french_locator_filter.toolbelt import PlgLogger, PlgOptionsManager

# ############################################################################
# ########## Classes ###############
# ##################################


class RestAPILocatorFilter(QgsGeocoderLocatorFilter):
    """Abstract class for QgsGeocoderLocatorFilter from a REST API

    Must implement at least these method:
    - _create_geocoder
    - name
    - displayName

    :param canvas: canvas used to display search result
    :type canvas: QgsMapCanvas
    """

    def __init__(self, canvas: Optional[QgsMapCanvas]):
        self.log = PlgLogger().log
        self.plg_settings = PlgOptionsManager.get_plg_settings()
        self._geocoder = self._create_geocoder()
        self._canvas = canvas
        super().__init__(
            name=self.name(),
            displayName=self.name(),  # Can't call displayName from implementation for tr use
            prefix=self.prefix(),
            geocoder=self._geocoder,
            canvas=canvas,
        )

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
        iface.showOptionsDialog(parent=parent, currentPage=f"mOptionsPage{__title__}")

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

        super().fetchResults(search, context, feedback)
