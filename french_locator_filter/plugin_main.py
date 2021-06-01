#! python3  # noqa: E265

"""
    Main plugin module.
"""

# PyQGIS
from qgis.gui import QgisInterface

# project
from french_locator_filter.__about__ import __title__, __version__
from french_locator_filter.core import FrenchBanGeocoderLocatorFilter
from french_locator_filter.toolbelt import PlgLogger

# ############################################################################
# ########## Classes ###############
# ##################################


class LocatorFilterPlugin:
    def __init__(self, iface: QgisInterface):
        """Constructor.

        :param iface: An interface instance that will be passed to this class which \
        provides the hook by which you can manipulate the QGIS application at run time.
        :type iface: QgsInterface
        """
        self.iface = iface
        self.log = PlgLogger().log

        # install locator filter
        self.filter = FrenchBanGeocoderLocatorFilter(self.iface)
        self.iface.registerLocatorFilter(self.filter)

        if __debug__:
            self.log(
                message=(
                    "DEBUG - French (BAN Geocoder) Locator Filter"
                    f" ({__title__} {__version__}) installed."
                ),
                log_level=4,
            )

    def initGui(self):
        """Set up plugin UI elements."""
        pass

    def unload(self):
        """Cleans up when plugin is disabled/uninstalled."""
        self.iface.deregisterLocatorFilter(self.filter)
