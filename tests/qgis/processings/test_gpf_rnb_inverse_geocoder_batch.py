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

from french_locator_filter.processing.gpf_rnb_inverse_geocoder_batch_processing import (
    GpfRnbInverseGeocoderBatchProcessing,
)
from french_locator_filter.processing.provider import FrenchLocatorProcessingProvider

RNB_SRV_MOCK_RESPOND = {
    "next": None,
    "previous": None,
    "results": [
        {
            "rnb_id": "RSJ5HEMCP3D3",
            "status": "constructed",
            "point": {
                "type": "Point",
                "coordinates": [2.354352867209375, 48.85210190224262],
            },
            "shape": {
                "type": "MultiPolygon",
                "coordinates": [
                    [
                        [
                            [2.354, 48.852],
                            [2.355, 48.852],
                            [2.355, 48.853],
                            [2.354, 48.853],
                            [2.354, 48.852],
                        ]
                    ]
                ],
            },
            "addresses": [
                {
                    "id": "75104_5599_00007",
                    "ban_id": None,
                    "source": "bdnb",
                    "street_number": "7",
                    "street_rep": None,
                    "street": "Rue Le Regrattier",
                    "city_name": "Paris 4e Arrondissement",
                    "city_zipcode": "75004",
                    "city_insee_code": "75104",
                }
            ],
            "ext_ids": [],
            "is_active": True,
            "validated_by": [],
        }
    ],
}

GEOCODING_RESULT_ATTRIBUTES = {
    "rnb_id": "RSJ5HEMCP3D3",
    "status": "constructed",
    "ban_id": "75104_5599_00007",
    "street_number": "7",
    "street": "Rue Le Regrattier",
    "city_name": "Paris 4e Arrondissement",
    "city_zipcode": "75004",
    "city_insee_code": "75104",
    "address_label": "7 Rue Le Regrattier, 75004 Paris 4e Arrondissement",
}


@pytest.fixture()
def alg() -> QgsProcessingAlgorithm:
    """Retrieve algorithm to be tested from processing registry

    :return: algorithm to be tested
    :rtype: QgsProcessingAlgorithm
    """
    algo_str = (
        f"{FrenchLocatorProcessingProvider().id()}:"
        f"{GpfRnbInverseGeocoderBatchProcessing().name()}"
    )
    alg = QgsApplication.processingRegistry().algorithmById(algo_str)
    assert alg is not None
    return alg


def test_inverse_geocode_with_input(
    rnb_srv: pytest_httpserver.HTTPServer, alg: QgsProcessingAlgorithm
):
    """Test reverse RNB geocoding with a feature, checking the address enrichment
    embedded directly in the RNB response

    :param alg: geocoding algorithm
    :type alg: QgsProcessingAlgorithm
    """

    rnb_srv.expect_oneshot_request("/buildings/", method="GET").respond_with_json(
        RNB_SRV_MOCK_RESPOND
    )

    input_layer = QgsVectorLayer(
        "Point",
        "test",
        "memory",
    )

    pr = input_layer.dataProvider()
    feat = QgsFeature()
    feat.setGeometry(
        QgsGeometry.fromPointXY(QgsPointXY(2.354352867209375, 48.85210190224262))
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
    assert output_layer.crs().authid() == "EPSG:4326"

    features = [f for f in output_layer.getFeatures()]
    geocoded_point = features[0].geometry().asPoint()

    assert geocoded_point.x() == pytest.approx(2.354352867209375)
    assert geocoded_point.y() == pytest.approx(48.85210190224262)

    expected_attributes = [GEOCODING_RESULT_ATTRIBUTES]
    for i, f in enumerate(output_layer.getFeatures()):
        for key, value in expected_attributes[i].items():
            assert f.attribute(key) == value
