import pytest
import pytest_httpserver
from qgis.core import QgsApplication

from french_locator_filter.processing.provider import FrenchLocatorProcessingProvider
from french_locator_filter.toolbelt.preferences import PlgSettingsStructure

GPF_SRV_URL = "http://localhost:5000/"
PHOTON_SRV_URL = "http://localhost:6000/"


@pytest.fixture(autouse=True)
def add_provider(qgis_processing) -> FrenchLocatorProcessingProvider:
    """
    Add GeoplateformeProvider to processing registry and remove it after use

    Args:
        qgis_processing: pytest-qgis fixture to initialize qgis processing
    """
    prov = FrenchLocatorProcessingProvider()
    QgsApplication.processingRegistry().addProvider(prov)
    yield prov
    QgsApplication.processingRegistry().removeProvider(prov)


def start_srv(host: str, port: int) -> pytest_httpserver.HTTPServer:
    """Start simulating a server with pytest_httpserver
    Server is stopped after use

    :param host: server host
    :type host: str
    :param port: server port
    :type port: int
    :yield: server started
    :rtype: pytest_httpserver.HTTPServer
    """
    server = pytest_httpserver.HTTPServer(host=host, port=port, ssl_context=None)
    server.start()
    yield server
    server.clear()
    if server.is_running():
        server.stop()


@pytest.fixture
def data_geopf_srv(monkeypatch) -> pytest_httpserver.HTTPServer:
    """Fixture to start simulating data.geopf.fr server and monkeypatch plugin settings for url

    :param monkeypatch: monkeypatch for PlgSettingsStructure
    :type monkeypatch: MonkeyPatch
    :yield: server started
    :rtype: pytest_httpserver.HTTPServer
    """
    server = start_srv("127.0.0.1", 5000)
    monkeypatch.setattr(PlgSettingsStructure, "request_url", GPF_SRV_URL)
    yield from server


@pytest.fixture
def photon_srv(monkeypatch) -> pytest_httpserver.HTTPServer:
    """Fixture to start simulating photon.komoot.io server and monkeypatch plugin settings for url

    :param monkeypatch: monkeypatch for PlgSettingsStructure
    :type monkeypatch: MonkeyPatch
    :yield: server started
    :rtype: pytest_httpserver.HTTPServer
    """
    server = start_srv("127.0.0.1", 5000)
    monkeypatch.setattr(PlgSettingsStructure, "request_photon_url", PHOTON_SRV_URL)
    yield from server
