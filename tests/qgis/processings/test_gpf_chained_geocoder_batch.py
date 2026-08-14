import json

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
from werkzeug.wrappers import Response

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

IDU = "75104000AV0117"

WFS_LIEN_ADRESSE_PARCELLE_RESPOND = {
    "type": "FeatureCollection",
    "features": [
        {
            "type": "Feature",
            "geometry": {"type": "LineString", "coordinates": [[2.354, 48.852], [2.3545, 48.8525]]},
            "properties": {
                "id_adr": "75104_5599_00007",
                "idu": IDU,
                "type_lien": "GEO",
                "nb_adr": 1,
                "nb_parc": 1,
            },
        }
    ],
}

WFS_LIEN_BATI_PARCELLE_RESPOND = {
    "type": "FeatureCollection",
    "features": [
        {
            "type": "Feature",
            "geometry": {"type": "LineString", "coordinates": [[2.354, 48.852], [2.3545, 48.8525]]},
            "properties": {
                "id_bat": "BATIMENT0000000245184192",
                "idu": IDU,
                "type_lien": "GEO",
                "nb_bat": 1,
                "nb_parc": 1,
            },
        }
    ],
}

WFS_PARCELLE_RESPOND = {
    "type": "FeatureCollection",
    "features": [
        {
            "type": "Feature",
            "geometry": {
                "type": "MultiPolygon",
                "coordinates": [[[[2.354, 48.852], [2.355, 48.852], [2.355, 48.853], [2.354, 48.853], [2.354, 48.852]]]],
            },
            "properties": {
                "idu": IDU,
                "section": "AV",
                "numero": "0117",
                "feuille": 1,
                "contenance": 245,
                "nom_com": "Paris 4e Arrondissement",
                "code_insee": "75104",
            },
        }
    ],
}

WFS_BATIMENT_RESPOND = {
    "type": "FeatureCollection",
    "features": [
        {
            "type": "Feature",
            "geometry": {
                "type": "MultiPolygon",
                "coordinates": [[[[2.3544, 48.8524], [2.3546, 48.8524], [2.3546, 48.8526], [2.3544, 48.8526], [2.3544, 48.8524]]]],
            },
            "properties": {
                "gid": 10643495,
                "type": "Bâtiment en dur",
                "code_dep": "75",
                "code_insee": "75104",
            },
        }
    ],
}

RNB_BUILDINGS_ON_PLOT_RESPOND = {
    "next": None,
    "previous": None,
    "results": [
        {
            "rnb_id": "RBJ8E9C42GDJ",
            "status": "constructed",
            "point": {"type": "Point", "coordinates": [2.35405, 48.85238]},
            "shape": None,
            "addresses": [],
        },
        {
            "rnb_id": "S65V7NJE3NKS",
            "status": "constructed",
            "point": {"type": "Point", "coordinates": [2.35401, 48.85229]},
            "shape": None,
            "addresses": [],
        },
    ],
}


def _wfs_handler(request):
    """Dispatch the mocked WFS response based on the requested TYPENAMES"""
    typenames = request.args.get("TYPENAMES", "")
    if "lien_adresse_parcelle" in typenames:
        body = WFS_LIEN_ADRESSE_PARCELLE_RESPOND
    elif "lien_bati_parcelle" in typenames:
        body = WFS_LIEN_BATI_PARCELLE_RESPOND
    elif "batiment" in typenames:
        body = WFS_BATIMENT_RESPOND
    elif "parcelle" in typenames:
        body = WFS_PARCELLE_RESPOND
    else:
        body = {"type": "FeatureCollection", "features": []}
    return Response(json.dumps(body), content_type="application/json")


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


def test_geocode_fans_out_one_result_per_building(
    data_geopf_srv: pytest_httpserver.HTTPServer,
    wfs_srv: pytest_httpserver.HTTPServer,
    rnb_srv: pytest_httpserver.HTTPServer,
    alg: QgsProcessingAlgorithm,
):
    """A single input address whose parcel has two RNB buildings must
    produce two output features.

    :param alg: geocoding algorithm
    :type alg: QgsProcessingAlgorithm
    """
    data_geopf_srv.expect_oneshot_request("/search", method="GET").respond_with_json(
        GPF_ADDRESS_SRV_MOCK_RESPOND
    )
    wfs_srv.expect_request("/", method="GET").respond_with_handler(_wfs_handler)
    rnb_srv.expect_oneshot_request(
        f"/buildings/plot/{IDU}/", method="GET"
    ).respond_with_json(RNB_BUILDINGS_ON_PLOT_RESPOND)

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

    rnb_ids = {f.attribute("building_rnb_id") for f in output_layer.getFeatures()}
    assert rnb_ids == {"RBJ8E9C42GDJ", "S65V7NJE3NKS"}
    for f in output_layer.getFeatures():
        assert f.attribute("address_label") == "7 Rue Le Regrattier 75004 Paris"
        assert f.attribute("parcel_idu") == IDU
        assert f.attribute("parcel_section") == "AV"
        assert f.attribute("building_ext_bdtopo_id") == "BATIMENT0000000245184192"
        assert f.attribute("building_cadastral_ids") == "10643495"
