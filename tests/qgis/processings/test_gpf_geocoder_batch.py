import copy

import pytest
import pytest_httpserver
from qgis.core import (
    QgsApplication,
    QgsFeature,
    QgsProcessingAlgorithm,
    QgsProcessingContext,
    QgsProcessingFeedback,
    QgsVectorLayer,
)

from french_locator_filter.processing.gpf_geocoder_batch_processing import (
    GpfGeocoderBatchProcessing,
)
from french_locator_filter.processing.provider import FrenchLocatorProcessingProvider

GPF_SRV_MOCK_RESPOND = {
    "type": "FeatureCollection",
    "features": [
        {
            "type": "Feature",
            "geometry": {"type": "Point", "coordinates": [5.405, 43.282]},
            "properties": {
                "label": "Marseille",
                "score": 0.9662990909090908,
                "id": "13055",
                "type": "municipality",
                "name": "Marseille",
                "postcode": "13001",
                "citycode": "13055",
                "x": 895296.11,
                "y": 6245510.5,
                "population": 877215,
                "city": "Marseille",
                "context": "13, Bouches-du-Rhône, Provence-Alpes-Côte d'Azur",
                "importance": 0.62929,
                "municipality": "Marseille",
                "_type": "address",
            },
        }
    ],
    "query": "Marseille",
}

GEOCODING_RESULT_ATTRIBUTES = {
    "label": "Marseille",
    "score": "0.9662990909090908",
    "id": "13055",
    "type": "municipality",
    "name": "Marseille",
    "postcode": "13001",
    "citycode": "13055",
    "x": "895296.11",
    "y": "6245510.5",
    "population": "877215",
    "city": "Marseille",
    "context": "13, Bouches-du-Rhône, Provence-Alpes-Côte d'Azur",
    "importance": "0.62929",
    "municipality": "Marseille",
}


@pytest.fixture()
def alg() -> QgsProcessingAlgorithm:
    """Retrieve algorithm to be tested from processing registry

    :return: algorithm to be tested
    :rtype: QgsProcessingAlgorithm
    """
    algo_str = f"{FrenchLocatorProcessingProvider().id()}:{GpfGeocoderBatchProcessing().name()}"
    alg = QgsApplication.processingRegistry().algorithmById(algo_str)
    assert alg is not None
    return alg


def test_geocode_no_input(alg: QgsProcessingAlgorithm):
    """Test geocode without features in input

    :param alg: _description_
    :type alg: QgsProcessingAlgorithm
    """
    input_layer = QgsVectorLayer(
        "NoGeometry?field=adresse:string",
        "test",
        "memory",
    )

    params = {"INPUT": input_layer, "FIELD": "adresse", "OUTPUT": "TEMPORARY_OUTPUT"}

    context = QgsProcessingContext()
    feedback = QgsProcessingFeedback()

    result, success = alg.run(params, context, feedback)
    assert success

    output_layer = context.getMapLayer(result["OUTPUT"])
    assert output_layer.isValid()
    assert output_layer.featureCount() == input_layer.featureCount()


def test_geocode_with_input(
    data_geopf_srv: pytest_httpserver.HTTPServer, alg: QgsProcessingAlgorithm
):
    """Test geocoding with a feature

    :param alg: geocoding algorithm
    :type alg: QgsProcessingAlgorithm
    """

    # Respond with mock
    data_geopf_srv.expect_oneshot_request("/search", method="GET").respond_with_json(
        GPF_SRV_MOCK_RESPOND
    )

    input_layer = QgsVectorLayer(
        "NoGeometry?field=adresse:string",
        "test",
        "memory",
    )

    pr = input_layer.dataProvider()
    feat = QgsFeature()
    feat.setAttributes(["Marseille"])
    pr.addFeatures([feat])

    params = {"INPUT": input_layer, "FIELD": "adresse", "OUTPUT": "TEMPORARY_OUTPUT"}

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

    expected_attributes = [GEOCODING_RESULT_ATTRIBUTES]
    for i, f in enumerate(output_layer.getFeatures()):
        for key, value in expected_attributes[i].items():
            assert f.attribute(key) == value


def test_geocode_with_crs(
    data_geopf_srv: pytest_httpserver.HTTPServer, alg: QgsProcessingAlgorithm
):
    """Test geocoding with CRS different than 4326. Input CRS should be kept

    :param alg: geocoding algorithm
    :type alg: QgsProcessingAlgorithm
    """

    # Respond with mock
    data_geopf_srv.expect_oneshot_request("/search", method="GET").respond_with_json(
        GPF_SRV_MOCK_RESPOND
    )

    input_layer = QgsVectorLayer(
        "Point?&crs=EPSG:3857&field=adresse:string",
        "test",
        "memory",
    )

    pr = input_layer.dataProvider()
    feat = QgsFeature()
    feat.setAttributes(["Marseille"])
    pr.addFeatures([feat])

    params = {"INPUT": input_layer, "FIELD": "adresse", "OUTPUT": "TEMPORARY_OUTPUT"}

    context = QgsProcessingContext()
    feedback = QgsProcessingFeedback()

    result, success = alg.run(params, context, feedback, catchExceptions=False)
    assert success

    output_layer = context.getMapLayer(result["OUTPUT"])
    assert output_layer.isValid()
    assert output_layer.featureCount() == input_layer.featureCount()
    assert output_layer.crs().authid() == input_layer.crs().authid()

    features = [f for f in output_layer.getFeatures()]
    geocoded_point = features[0].geometry().asPoint()

    assert geocoded_point.x() == pytest.approx(601681.84773764363490045)
    assert geocoded_point.y() == pytest.approx(5354994.10118988063186407)

    expected_attributes = [GEOCODING_RESULT_ATTRIBUTES]
    for i, f in enumerate(output_layer.getFeatures()):
        for key, value in expected_attributes[i].items():
            assert f.attribute(key) == value


def test_geocode_available_attributes(
    data_geopf_srv: pytest_httpserver.HTTPServer, alg: QgsProcessingAlgorithm
):
    """Test geocoding returned attributes

    :param alg: geocoding algorithm
    :type alg: QgsProcessingAlgorithm
    """

    # Respond with mock
    data_geopf_srv.expect_oneshot_request("/search", method="GET").respond_with_json(
        GPF_SRV_MOCK_RESPOND
    )

    input_layer = QgsVectorLayer(
        "NoGeometry?field=adresse:string",
        "test",
        "memory",
    )

    pr = input_layer.dataProvider()
    feat = QgsFeature()
    feat.setAttributes(["Marseille"])
    pr.addFeatures([feat])

    params = {"INPUT": input_layer, "FIELD": "adresse", "OUTPUT": "TEMPORARY_OUTPUT"}

    context = QgsProcessingContext()
    feedback = QgsProcessingFeedback()

    result, success = alg.run(params, context, feedback, catchExceptions=False)
    assert success

    output_layer = context.getMapLayer(result["OUTPUT"])
    assert output_layer.isValid()
    assert output_layer.featureCount() == input_layer.featureCount()

    expected_attributes = [GEOCODING_RESULT_ATTRIBUTES]
    for i, f in enumerate(output_layer.getFeatures()):
        for key, value in expected_attributes[i].items():
            assert f.attribute(key) == value


def test_geocode_keep_attributes(
    data_geopf_srv: pytest_httpserver.HTTPServer, alg: QgsProcessingAlgorithm
):
    """Test that input attributes are kept

    :param alg: geocoding algorithm
    :type alg: QgsProcessingAlgorithm
    """

    # Respond with mock
    data_geopf_srv.expect_oneshot_request("/search", method="GET").respond_with_json(
        GPF_SRV_MOCK_RESPOND
    )

    input_layer = QgsVectorLayer(
        "NoGeometry?field=adresse:string&field=other_field:string",
        "test",
        "memory",
    )

    pr = input_layer.dataProvider()
    feat = QgsFeature()
    feat.setAttributes(["Marseille", "Other field value"])
    pr.addFeatures([feat])

    params = {"INPUT": input_layer, "FIELD": "adresse", "OUTPUT": "TEMPORARY_OUTPUT"}

    context = QgsProcessingContext()
    feedback = QgsProcessingFeedback()

    result, success = alg.run(params, context, feedback, catchExceptions=False)
    assert success

    output_layer = context.getMapLayer(result["OUTPUT"])
    assert output_layer.isValid()
    assert output_layer.featureCount() == input_layer.featureCount()
    assert output_layer.crs().authid() == "EPSG:4326"

    result = copy.deepcopy(GEOCODING_RESULT_ATTRIBUTES)
    result["other_field"] = "Other field value"
    expected_attributes = [result]
    for i, f in enumerate(output_layer.getFeatures()):
        for key, value in expected_attributes[i].items():
            assert f.attribute(key) == value
