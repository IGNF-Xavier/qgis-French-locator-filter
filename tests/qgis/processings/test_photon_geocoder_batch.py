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

from french_locator_filter.processing.photon_geocoder_batch_processing import (
    PhotonGeocoderBatchProcessing,
)
from french_locator_filter.processing.provider import FrenchLocatorProcessingProvider

PHOTON_SRV_MOCK_RESPOND = {
    "type": "FeatureCollection",
    "features": [
        {
            "type": "Feature",
            "properties": {
                "osm_type": "R",
                "osm_id": 76469,
                "osm_key": "place",
                "osm_value": "city",
                "type": "city",
                "postcode": "13000;13001;13002;13003;13004;13005;13006;13007;13008;13009;13010;13011;13012;13013;13014;13015;13016",
                "countrycode": "FR",
                "name": "Marseille",
                "county": "Bouches-du-Rhône",
                "state": "Provence-Alpes-Côte d'Azur",
                "country": "France",
                "extent": [5.2287864, 43.3910329, 5.5324758, 43.1696228],
            },
            "geometry": {"type": "Point", "coordinates": [5.3699525, 43.2961743]},
        }
    ],
}

GEOCODING_RESULT_ATTRIBUTES = {
    "osm_type": "R",
    "osm_id": 76469,
    "osm_key": "place",
    "osm_value": "city",
    "type": "city",
    "postcode": "13000;13001;13002;13003;13004;13005;13006;13007;13008;13009;13010;13011;13012;13013;13014;13015;13016",
    "countrycode": "FR",
    "name": "Marseille",
    "county": "Bouches-du-Rhône",
    "state": "Provence-Alpes-Côte d'Azur",
    "country": "France",
}


@pytest.fixture()
def alg() -> QgsProcessingAlgorithm:
    """Retrieve algorithm to be tested from processing registry

    :return: algorithm to be tested
    :rtype: QgsProcessingAlgorithm
    """
    algo_str = f"{FrenchLocatorProcessingProvider().id()}:{PhotonGeocoderBatchProcessing().name()}"
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
    photon_srv: pytest_httpserver.HTTPServer, alg: QgsProcessingAlgorithm
):
    """Test geocoding with a feature

    :param alg: geocoding algorithm
    :type alg: QgsProcessingAlgorithm
    """

    # Respond with mock
    photon_srv.expect_oneshot_request("/api", method="GET").respond_with_json(
        PHOTON_SRV_MOCK_RESPOND
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

    assert geocoded_point.x() == pytest.approx(5.3699525)
    assert geocoded_point.y() == pytest.approx(43.2961743)

    expected_attributes = [GEOCODING_RESULT_ATTRIBUTES]
    for i, f in enumerate(output_layer.getFeatures()):
        for key, value in expected_attributes[i].items():
            assert f.attribute(key) == value


def test_geocode_with_crs(
    photon_srv: pytest_httpserver.HTTPServer, alg: QgsProcessingAlgorithm
):
    """Test geocoding with CRS different than 4326. Input CRS should be kept

    :param alg: geocoding algorithm
    :type alg: QgsProcessingAlgorithm
    """

    # Respond with mock
    photon_srv.expect_oneshot_request("/api", method="GET").respond_with_json(
        PHOTON_SRV_MOCK_RESPOND
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

    assert geocoded_point.x() == pytest.approx(597780.3778840664)
    assert geocoded_point.y() == pytest.approx(5357161.800828047)

    expected_attributes = [GEOCODING_RESULT_ATTRIBUTES]
    for i, f in enumerate(output_layer.getFeatures()):
        for key, value in expected_attributes[i].items():
            assert f.attribute(key) == value


def test_geocode_available_attributes(
    photon_srv: pytest_httpserver.HTTPServer, alg: QgsProcessingAlgorithm
):
    """Test geocoding returned attributes

    :param alg: geocoding algorithm
    :type alg: QgsProcessingAlgorithm
    """

    # Respond with mock
    photon_srv.expect_oneshot_request("/api", method="GET").respond_with_json(
        PHOTON_SRV_MOCK_RESPOND
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
    photon_srv: pytest_httpserver.HTTPServer, alg: QgsProcessingAlgorithm
):
    """Test that input attributes are kept

    :param alg: geocoding algorithm
    :type alg: QgsProcessingAlgorithm
    """

    # Respond with mock
    photon_srv.expect_oneshot_request("/api", method="GET").respond_with_json(
        PHOTON_SRV_MOCK_RESPOND
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
