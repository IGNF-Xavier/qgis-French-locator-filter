import pytest
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

from french_locator_filter.processing.photon_inverse_geocoder_batch_processing import (
    PhotonInverseGeocoderBatchProcessing,
)
from french_locator_filter.processing.provider import FrenchLocatorProcessingProvider


@pytest.fixture()
def alg() -> QgsProcessingAlgorithm:
    """Retrieve algorithm to be tested from processing registry

    :return: algorithm to be tested
    :rtype: QgsProcessingAlgorithm
    """
    algo_str = f"{FrenchLocatorProcessingProvider().id()}:{PhotonInverseGeocoderBatchProcessing().name()}"
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


def test_inverse_geocode_with_input(alg: QgsProcessingAlgorithm):
    """Test geocoding with a feature

    :param alg: geocoding algorithm
    :type alg: QgsProcessingAlgorithm
    """
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

    assert geocoded_point.x() == pytest.approx(5.405081)
    assert geocoded_point.y() == pytest.approx(43.2819925)

    expected_attributes = [
        {
            "osm_id": "109075797",
            "country": "France",
            "city": "Marseille",
            "countrycode": "FR",
            "postcode": "13010",
            "locality": "La Capelette",
            "county": "Bouches-du-Rhône",
            "type": "street",
            "osm_type": "W",
            "osm_key": "highway",
            "district": "10th Arrondissement",
            "osm_value": "tertiary",
            "name": "Avenue Benjamin Delessert",
            "state": "Provence-Alpes-Côte d'Azur",
        }
    ]
    for i, f in enumerate(output_layer.getFeatures()):
        for key, value in expected_attributes[i].items():
            assert f.attribute(key) == value


def test_inverse_geocode_with_crs(alg: QgsProcessingAlgorithm):
    """Test geocoding with CRS different than 4326. Input CRS should be kept

    :param alg: geocoding algorithm
    :type alg: QgsProcessingAlgorithm
    """
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

    assert geocoded_point.x() == pytest.approx(601690.8646163979)
    assert geocoded_point.y() == pytest.approx(5354994.10118988)

    expected_attributes = [
        {
            "osm_id": "109075797",
            "country": "France",
            "city": "Marseille",
            "countrycode": "FR",
            "postcode": "13010",
            "locality": "La Capelette",
            "county": "Bouches-du-Rhône",
            "type": "street",
            "osm_type": "W",
            "osm_key": "highway",
            "district": "10th Arrondissement",
            "osm_value": "tertiary",
            "name": "Avenue Benjamin Delessert",
            "state": "Provence-Alpes-Côte d'Azur",
        }
    ]
    for i, f in enumerate(output_layer.getFeatures()):
        for key, value in expected_attributes[i].items():
            assert f.attribute(key) == value


def test_geocode_keep_attributes(alg: QgsProcessingAlgorithm):
    """Test that input attributes are kept

    :param alg: geocoding algorithm
    :type alg: QgsProcessingAlgorithm
    """
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

    expected_attributes = [
        {
            "osm_id": "109075797",
            "country": "France",
            "city": "Marseille",
            "countrycode": "FR",
            "postcode": "13010",
            "locality": "La Capelette",
            "county": "Bouches-du-Rhône",
            "type": "street",
            "osm_type": "W",
            "osm_key": "highway",
            "district": "10th Arrondissement",
            "osm_value": "tertiary",
            "name": "Avenue Benjamin Delessert",
            "state": "Provence-Alpes-Côte d'Azur",
            "other_field": "Other field value",
        }
    ]
    for i, f in enumerate(output_layer.getFeatures()):
        for key, value in expected_attributes[i].items():
            assert f.attribute(key) == value
