import pytest
import pytest_httpserver
from qgis.core import QgsApplication

from french_locator_filter.processing.provider import FrenchLocatorProcessingProvider
from french_locator_filter.toolbelt.preferences import PlgSettingsStructure


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


@pytest.fixture(scope="function")
def data_geopf_srv(monkeypatch) -> pytest_httpserver.HTTPServer:
    """Fixture to start simulating data.geopf.fr server and monkeypatch plugin settings for url

    :param monkeypatch: monkeypatch for PlgSettingsStructure
    :type monkeypatch: MonkeyPatch
    :yield: server started
    :rtype: pytest_httpserver.HTTPServer
    """
    server = pytest_httpserver.HTTPServer()
    server.start()
    monkeypatch.setattr(PlgSettingsStructure, "gpf_url", server.url_for(""))
    yield server
    server.clear()
    if server.is_running():
        server.stop()


@pytest.fixture(scope="function")
def photon_srv(monkeypatch) -> pytest_httpserver.HTTPServer:
    """Fixture to start simulating photon.komoot.io server and monkeypatch plugin settings for url

    :param monkeypatch: monkeypatch for PlgSettingsStructure
    :type monkeypatch: MonkeyPatch
    :yield: server started
    :rtype: pytest_httpserver.HTTPServer
    """
    server = pytest_httpserver.HTTPServer()
    server.start()
    monkeypatch.setattr(PlgSettingsStructure, "photon_url", server.url_for(""))
    yield server
    server.clear()
    if server.is_running():
        server.stop()


@pytest.fixture(scope="function")
def rnb_srv(monkeypatch) -> pytest_httpserver.HTTPServer:
    """Fixture to start simulating rnb-api.beta.gouv.fr server and monkeypatch plugin settings for url

    :param monkeypatch: monkeypatch for PlgSettingsStructure
    :type monkeypatch: MonkeyPatch
    :yield: server started
    :rtype: pytest_httpserver.HTTPServer
    """
    server = pytest_httpserver.HTTPServer()
    server.start()
    monkeypatch.setattr(PlgSettingsStructure, "rnb_url", server.url_for(""))
    yield server
    server.clear()
    if server.is_running():
        server.stop()
