import pytest
from qgis.core import QgsApplication

from french_locator_filter.processing.provider import FrenchLocatorProcessingProvider


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
