#! python3  # noqa: E265


def classFactory(iface):  # pylint: disable=invalid-name
    """Load NominatimFilterPlugin class from file nominatimfilter.

    :param iface: A QGIS interface instance.
    :type iface: QgsInterface
    """
    _ = iface
    from .plugin_main import FrenchGeocoderLocatorFilterPlugin

    return FrenchGeocoderLocatorFilterPlugin()
