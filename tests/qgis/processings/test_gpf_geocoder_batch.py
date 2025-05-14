import pytest
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


def test_geocode_with_input(alg: QgsProcessingAlgorithm):
    """Test geocoding with a feature

    :param alg: geocoding algorithm
    :type alg: QgsProcessingAlgorithm
    """
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


def test_geocode_with_crs(alg: QgsProcessingAlgorithm):
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


def test_geocode_available_attributes(alg: QgsProcessingAlgorithm):
    """Test geocoding returned attributes

    :param alg: geocoding algorithm
    :type alg: QgsProcessingAlgorithm
    """
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

    features = [f for f in output_layer.getFeatures()]
    assert features[0].attribute("adresse") == "Marseille"
    assert features[0].attribute("type") == "municipality"
    assert features[0].attribute("name") == "Marseille"
    assert features[0].attribute("postcode") == "13001"
    assert features[0].attribute("citycode") == "13055"
    assert features[0].attribute("city") == "Marseille"
    assert features[0].attribute("district") is None
    assert features[0].attribute("housenumber") is None
    assert features[0].attribute("street") is None
    # No check of population, result could change assert features[0].attribute("population") == 877215
    assert (
        features[0].attribute("context")
        == "13, Bouches-du-Rhône, Provence-Alpes-Côte d'Azur"
    )
    assert features[0].attribute("municipality") == "Marseille"
    assert features[0].attribute("oldcitycode") is None
    assert features[0].attribute("oldcity") is None
    assert features[0].attribute("label") == "Marseille"
    # No check of importance, result could change assert features[0].attribute("importance") == 0.62929


def test_geocode_keep_attributes(alg: QgsProcessingAlgorithm):
    """Test that input attributes are kept

    :param alg: geocoding algorithm
    :type alg: QgsProcessingAlgorithm
    """
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

    features = [f for f in output_layer.getFeatures()]
    assert features[0].attribute("adresse") == "Marseille"
    assert features[0].attribute("other_field") == "Other field value"
