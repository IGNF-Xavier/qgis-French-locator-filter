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

from french_locator_filter.processing.gpf_chained_inverse_geocoder_batch_processing import (
    GpfChainedInverseGeocoderBatchProcessing,
)
from french_locator_filter.processing.provider import FrenchLocatorProcessingProvider

# one building intersecting two cadastral parcels, with its embedded address
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
            "shape": None,
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
            "plots": [
                {"id": "75104000AV0108", "bdg_cover_ratio": 0.20776904571469965},
                {"id": "75104000AV0109", "bdg_cover_ratio": 0.7712328321391224},
            ],
            "ext_ids": [],
            "is_active": True,
            "validated_by": [],
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
        f"{GpfChainedInverseGeocoderBatchProcessing().name()}"
    )
    alg = QgsApplication.processingRegistry().algorithmById(algo_str)
    assert alg is not None
    return alg


def test_inverse_geocode_fans_out_one_result_per_parcel(
    rnb_srv: pytest_httpserver.HTTPServer, alg: QgsProcessingAlgorithm
):
    """A single clicked point whose building intersects two parcels must
    produce two output features, with the address read from RNB.

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

    params = {
        "INPUT": input_layer,
        "NB_RESULT_BY_FEATURE": 30,
        "OUTPUT": "TEMPORARY_OUTPUT",
    }

    context = QgsProcessingContext()
    feedback = QgsProcessingFeedback()

    result, success = alg.run(params, context, feedback, catchExceptions=False)
    assert success

    output_layer = context.getMapLayer(result["OUTPUT"])
    assert output_layer.isValid()
    assert output_layer.featureCount() == 2

    parcel_ids = {f.attribute("parcel_id") for f in output_layer.getFeatures()}
    assert parcel_ids == {"75104000AV0108", "75104000AV0109"}
    for f in output_layer.getFeatures():
        assert f.attribute("address_city") == "Paris 4e Arrondissement"
        assert f.attribute("building_rnb_id") == "RSJ5HEMCP3D3"
