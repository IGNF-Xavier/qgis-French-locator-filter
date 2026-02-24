import copy

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

from french_locator_filter.processing.gpf_inverse_geocoder_batch_processing import (
    GpfInverseGeocoderBatchProcessing,
)
from french_locator_filter.processing.provider import FrenchLocatorProcessingProvider

GPF_SRV_MOCK_RESPOND_LIMIT_1 = {
    "type": "FeatureCollection",
    "features": [
        {
            "type": "Feature",
            "geometry": {"type": "Point", "coordinates": [5.405, 43.282]},
            "properties": {
                "type": "municipality",
                "name": "Marseille",
                "postcode": "13001",
                "citycode": "13055",
                "city": "Marseille",
                "population": 877215,
                "context": "13, Bouches-du-Rhône, Provence-Alpes-Côte d'Azur",
                "importance": 0.62929,
                "id": "13055",
                "x": 895296.11,
                "y": 6245510.5,
                "label": "13001,13002,13003,13004,13005,13006,13007,13008,13009,13010,13011,13012,13013,13014,13015,13016 Marseille",
                "distance": 0,
                "score": 1,
                "_type": "address",
            },
        }
    ],
}

GPF_SRV_MOCK_RESPOND_LIMIT_2 = {
    "type": "FeatureCollection",
    "features": [
        {
            "type": "Feature",
            "geometry": {"type": "Point", "coordinates": [5.405, 43.282]},
            "properties": {
                "type": "municipality",
                "name": "Marseille",
                "postcode": "13001",
                "citycode": "13055",
                "city": "Marseille",
                "population": 877215,
                "context": "13, Bouches-du-Rhône, Provence-Alpes-Côte d'Azur",
                "importance": 0.62929,
                "id": "13055",
                "x": 895296.11,
                "y": 6245510.5,
                "label": "13001,13002,13003,13004,13005,13006,13007,13008,13009,13010,13011,13012,13013,13014,13015,13016 Marseille",
                "distance": 0,
                "score": 1,
                "_type": "address",
            },
        },
        {
            "type": "Feature",
            "geometry": {"type": "Point", "coordinates": [5.405016, 43.281979]},
            "properties": {
                "type": "housenumber",
                "name": "7 Avenue benjamin delessert",
                "label": "7 Avenue benjamin delessert 13010 Marseille",
                "street": "Avenue benjamin delessert",
                "postcode": "13010",
                "citycode": "13210",
                "city": "Marseille",
                "district": "Marseille 10e Arrondissement",
                "context": "13, Bouches-du-Rhône, Provence-Alpes-Côte d'Azur",
                "importance": 0.68649,
                "housenumber": "7",
                "id": "13210_1059_00007",
                "banId": "dd288924-294e-437a-b965-76e0fd3d2f01",
                "x": 895297.48,
                "y": 6245508.21,
                "distance": 3,
                "score": 0.9997,
                "_type": "address",
            },
        },
    ],
}

GEOCODING_RESULT_ATTRIBUTES = [
    {
        "type": "municipality",
        "name": "Marseille",
        "postcode": "13001",
        "citycode": "13055",
        "city": "Marseille",
        "population": "877215",
        "context": "13, Bouches-du-Rhône, Provence-Alpes-Côte d'Azur",
        "importance": "0.62929",
        "id": "13055",
        "x": "895296.11",
        "y": "6245510.5",
        "label": "13001,13002,13003,13004,13005,13006,13007,13008,13009,13010,13011,13012,13013,13014,13015,13016 Marseille",
        "score": "1",
    },
    {
        "type": "housenumber",
        "name": "7 Avenue benjamin delessert",
        "label": "7 Avenue benjamin delessert 13010 Marseille",
        "street": "Avenue benjamin delessert",
        "postcode": "13010",
        "citycode": "13210",
        "city": "Marseille",
        "district": "Marseille 10e Arrondissement",
        "context": "13, Bouches-du-Rhône, Provence-Alpes-Côte d'Azur",
        "importance": "0.68649",
        "housenumber": "7",
        "id": "13210_1059_00007",
        "x": "895297.48",
        "y": "6245508.21",
        "score": "0.9997",
    },
]


@pytest.fixture()
def alg() -> QgsProcessingAlgorithm:
    """Retrieve algorithm to be tested from processing registry

    :return: algorithm to be tested
    :rtype: QgsProcessingAlgorithm
    """
    algo_str = f"{FrenchLocatorProcessingProvider().id()}:{GpfInverseGeocoderBatchProcessing().name()}"
    alg = QgsApplication.processingRegistry().algorithmById(algo_str)
    assert alg is not None
    return alg


def test_geocode_no_input(alg: QgsProcessingAlgorithm):
    """Test geocode without features in input

    :param alg: _description_
    :type alg: QgsProcessingAlgorithm
    """
    input_layer = QgsVectorLayer(
        "NoGeometry",
        "test",
        "memory",
    )

    params = {"INPUT": input_layer, "OUTPUT": "TEMPORARY_OUTPUT"}

    context = QgsProcessingContext()
    feedback = QgsProcessingFeedback()

    result, success = alg.run(params, context, feedback)
    assert success

    output_layer = context.getMapLayer(result["OUTPUT"])
    assert output_layer.isValid()
    assert output_layer.featureCount() == input_layer.featureCount()


def test_inverse_geocode_with_input(
    data_geopf_srv: pytest_httpserver.HTTPServer, alg: QgsProcessingAlgorithm
):
    """Test geocoding with a feature

    :param alg: geocoding algorithm
    :type alg: QgsProcessingAlgorithm
    """

    # Respond with mock
    data_geopf_srv.expect_oneshot_request("/reverse", method="GET").respond_with_json(
        GPF_SRV_MOCK_RESPOND_LIMIT_1
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

    expected_attributes = GEOCODING_RESULT_ATTRIBUTES[0:1]
    for i, f in enumerate(output_layer.getFeatures()):
        for key, value in expected_attributes[i].items():
            assert f.attribute(key) == value


def test_inverse_geocode_multiple_result(
    data_geopf_srv: pytest_httpserver.HTTPServer, alg: QgsProcessingAlgorithm
):
    """Test geocoding with a feature

    :param alg: geocoding algorithm
    :type alg: QgsProcessingAlgorithm
    """

    # Respond with mock
    data_geopf_srv.expect_oneshot_request("/reverse", method="GET").respond_with_json(
        GPF_SRV_MOCK_RESPOND_LIMIT_2
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

    params = {
        "INPUT": input_layer,
        "NB_RESULT_BY_FEATURE": 2,
        "OUTPUT": "TEMPORARY_OUTPUT",
    }

    context = QgsProcessingContext()
    feedback = QgsProcessingFeedback()

    result, success = alg.run(params, context, feedback, catchExceptions=False)
    assert success

    output_layer = context.getMapLayer(result["OUTPUT"])
    assert output_layer.isValid()
    assert output_layer.featureCount() == input_layer.featureCount() * 2
    assert output_layer.crs().authid() == "EPSG:4326"

    features = [f for f in output_layer.getFeatures()]
    geocoded_point = features[0].geometry().asPoint()

    assert geocoded_point.x() == pytest.approx(5.405)
    assert geocoded_point.y() == pytest.approx(43.282)

    expected_attributes = copy.deepcopy(GEOCODING_RESULT_ATTRIBUTES)
    for i, f in enumerate(output_layer.getFeatures()):
        for key, value in expected_attributes[i].items():
            assert f.attribute(key) == value


def test_inverse_geocode_with_crs(
    data_geopf_srv: pytest_httpserver.HTTPServer, alg: QgsProcessingAlgorithm
):
    """Test geocoding with CRS different than 4326. Input CRS should be kept

    :param alg: geocoding algorithm
    :type alg: QgsProcessingAlgorithm
    """

    # Respond with mock
    data_geopf_srv.expect_oneshot_request("/reverse", method="GET").respond_with_json(
        GPF_SRV_MOCK_RESPOND_LIMIT_1
    )

    input_layer = QgsVectorLayer(
        "Point?&crs=EPSG:3857&field=adresse:string",
        "test",
        "memory",
    )

    pr = input_layer.dataProvider()
    feat = QgsFeature()
    feat.setGeometry(
        QgsGeometry.fromPointXY(
            QgsPointXY(601681.84773764363490045, 5354994.10118988063186407)
        )
    )
    pr.addFeatures([feat])

    params = {"INPUT": input_layer, "OUTPUT": "TEMPORARY_OUTPUT"}

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

    expected_attributes = GEOCODING_RESULT_ATTRIBUTES[0:1]
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
    data_geopf_srv.expect_oneshot_request("/reverse", method="GET").respond_with_json(
        GPF_SRV_MOCK_RESPOND_LIMIT_1
    )

    input_layer = QgsVectorLayer(
        "Point?field=other_field:string",
        "test",
        "memory",
    )

    pr = input_layer.dataProvider()
    feat = QgsFeature()
    feat.setAttributes(["Other field value"])
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

    result = copy.deepcopy(GEOCODING_RESULT_ATTRIBUTES[0])
    result["other_field"] = "Other field value"
    expected_attributes = [result]
    for i, f in enumerate(output_layer.getFeatures()):
        for key, value in expected_attributes[i].items():
            assert f.attribute(key) == value
