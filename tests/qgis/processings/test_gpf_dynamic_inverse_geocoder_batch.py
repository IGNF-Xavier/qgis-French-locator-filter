import pytest
import pytest_httpserver
from qgis.core import (
    QgsApplication,
    QgsFeature,
    QgsGeometry,
    QgsPointXY,
    QgsProcessingAlgorithm,
    QgsProcessingContext,
    QgsProcessingFeedback,
    QgsVectorLayer,
)

from french_locator_filter.processing.gpf_dynamic_inverse_geocoder_batch_processing import (
    GpfDynamicInverseGeocoderBatchProcessing,
)
from french_locator_filter.processing.provider import FrenchLocatorProcessingProvider

# default settings (empty request_indexes) restrict the dynamic geocoder to the
# "address" index
GPF_SRV_MOCK_RESPOND = {
    "type": "FeatureCollection",
    "features": [
        {
            "type": "Feature",
            "geometry": {"type": "Point", "coordinates": [5.405, 43.282]},
            "properties": {
                "label": "Marseille",
                "score": 1,
                "id": "13055",
                "type": "municipality",
                "city": "Marseille",
                "citycode": "13055",
                "_type": "address",
            },
        }
    ],
}


@pytest.fixture()
def alg() -> QgsProcessingAlgorithm:
    """Retrieve algorithm to be tested from processing registry

    :return: algorithm to be tested
    :rtype: QgsProcessingAlgorithm
    """
    algo_str = (
        f"{FrenchLocatorProcessingProvider().id()}:"
        f"{GpfDynamicInverseGeocoderBatchProcessing().name()}"
    )
    alg = QgsApplication.processingRegistry().algorithmById(algo_str)
    assert alg is not None
    return alg


def test_inverse_geocode_with_input(
    data_geopf_srv: pytest_httpserver.HTTPServer, alg: QgsProcessingAlgorithm
):
    """Test reverse geocoding with the default (address) active index

    :param alg: geocoding algorithm
    :type alg: QgsProcessingAlgorithm
    """
    data_geopf_srv.expect_oneshot_request("/reverse", method="GET").respond_with_json(
        GPF_SRV_MOCK_RESPOND
    )

    input_layer = QgsVectorLayer(
        "Point",
        "test",
        "memory",
    )

    pr = input_layer.dataProvider()
    feat = QgsFeature()
    feat.setGeometry(QgsGeometry.fromPointXY(QgsPointXY(5.405, 43.282)))
    pr.addFeatures([feat])

    params = {"INPUT": input_layer, "OUTPUT": "TEMPORARY_OUTPUT"}

    context = QgsProcessingContext()
    feedback = QgsProcessingFeedback()

    result, success = alg.run(params, context, feedback, catchExceptions=False)
    assert success

    output_layer = context.getMapLayer(result["OUTPUT"])
    assert output_layer.isValid()
    assert output_layer.featureCount() == input_layer.featureCount()
    assert output_layer.crs().authid() == "EPSG:4326"

    features = [f for f in output_layer.getFeatures()]
    geocoded_point = features[0].geometry().asPoint()

    assert geocoded_point.x() == pytest.approx(5.405)
    assert geocoded_point.y() == pytest.approx(43.282)
    assert features[0].attribute("label") == "Marseille"
