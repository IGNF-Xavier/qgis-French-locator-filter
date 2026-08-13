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

from french_locator_filter.processing.gpf_chained_geocoder_batch_processing import (
    GpfChainedGeocoderBatchProcessing,
)
from french_locator_filter.processing.provider import FrenchLocatorProcessingProvider

GPF_ADDRESS_SRV_MOCK_RESPOND = {
    "type": "FeatureCollection",
    "features": [
        {
            "type": "Feature",
            "geometry": {
                "type": "Point",
                "coordinates": [2.354352867209375, 48.85210190224262],
            },
            "properties": {
                "type": "housenumber",
                "label": "7 Rue Le Regrattier 75004 Paris",
                "id": "75104_5599_00007",
                "city": "Paris",
                "postcode": "75004",
                "citycode": "75104",
                "housenumber": "7",
                "street": "Rue Le Regrattier",
                "score": 0.9,
            },
        }
    ],
}

# one building intersecting two cadastral parcels (real RNB example, withPlots=1)
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
            "addresses": [],
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
        f"{GpfChainedGeocoderBatchProcessing().name()}"
    )
    alg = QgsApplication.processingRegistry().algorithmById(algo_str)
    assert alg is not None
    return alg


def test_geocode_fans_out_one_result_per_parcel(
    data_geopf_srv: pytest_httpserver.HTTPServer,
    rnb_srv: pytest_httpserver.HTTPServer,
    alg: QgsProcessingAlgorithm,
):
    """A single input address whose building intersects two parcels must
    produce two output features.

    :param alg: geocoding algorithm
    :type alg: QgsProcessingAlgorithm
    """
    data_geopf_srv.expect_oneshot_request("/search", method="GET").respond_with_json(
        GPF_ADDRESS_SRV_MOCK_RESPOND
    )
    rnb_srv.expect_oneshot_request("/buildings/", method="GET").respond_with_json(
        RNB_SRV_MOCK_RESPOND
    )

    input_layer = QgsVectorLayer(
        "NoGeometry?field=adresse:string",
        "test",
        "memory",
    )

    pr = input_layer.dataProvider()
    feat = QgsFeature()
    feat.setAttributes(["7 Rue Le Regrattier 75004 Paris"])
    pr.addFeatures([feat])

    params = {"INPUT": input_layer, "FIELD": "adresse", "OUTPUT": "TEMPORARY_OUTPUT"}

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
        assert f.attribute("address_label") == "7 Rue Le Regrattier 75004 Paris"
        assert f.attribute("building_rnb_id") == "RSJ5HEMCP3D3"
