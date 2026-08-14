#! python3  # noqa E265

"""
Usage from the repo root folder:

.. code-block:: bash

    # for whole tests
    python -m unittest tests.qgis.test_gpf_chained_geocoder
"""

# standard library
import unittest

# PyQGIS
from qgis.core import (
    QgsCoordinateReferenceSystem,
    QgsGeocoderResult,
    QgsGeometry,
    QgsPointXY,
)

# project
from french_locator_filter.core.geocoder.gpf_chained_geocoder import (
    WFS_BATIMENT,
    WFS_PARCELLE,
    GpfChainedGeocoder,
    _polygon_wkt_lat_lon,
)

# ############################################################################
# ########## Classes #############
# ################################

ADDRESS_FIELDS = {
    "address_label": "7 Rue Le Regrattier 75004 Paris",
    "address_id": "75104_5599_00007",
    "address_postcode": "75004",
    "address_citycode": "75104",
    "address_city": "Paris",
    "address_housenumber": "7",
    "address_street": "Rue Le Regrattier",
}

# real WFS parcelle feature example (CADASTRALPARCELS.PARCELLAIRE_EXPRESS:parcelle)
PARCEL_FEATURE = {
    "type": "Feature",
    "geometry": {
        "type": "MultiPolygon",
        "coordinates": [[[[2.354, 48.852], [2.355, 48.852], [2.355, 48.853], [2.354, 48.853], [2.354, 48.852]]]],
    },
    "properties": {
        "idu": "75104000AV0117",
        "section": "AV",
        "numero": "0117",
        "feuille": 1,
        "contenance": 245,
        "nom_com": "Paris 4e Arrondissement",
        "code_insee": "75104",
    },
}

# real RNB /buildings/plot/{idu}/ example: two buildings on the same parcel
BUILDING_1 = {
    "rnb_id": "RBJ8E9C42GDJ",
    "status": "constructed",
    "point": {"type": "Point", "coordinates": [2.354053843528745, 48.85238387801971]},
    "shape": None,
    "addresses": [],
    "ext_ids": [
        {"id": "BATIMENT0000000245184192", "source": "bdtopo"},
        {"id": "bdnb-bc-XXXX-YYYY", "source": "bdnb"},
    ],
}
BUILDING_2 = {
    "rnb_id": "S65V7NJE3NKS",
    "status": "constructed",
    "point": {"type": "Point", "coordinates": [2.354010816155664, 48.85229519541175]},
    "shape": None,
    "addresses": [],
    "ext_ids": [],
}

# PCI "bâti parcellaire" candidates (CADASTRALPARCELS.PARCELLAIRE_EXPRESS:batiment):
# one inside the parcel, one far away (must be excluded by the intersection test)
CADASTRAL_BUILDING_INSIDE = {
    "type": "Feature",
    "geometry": {
        "type": "MultiPolygon",
        "coordinates": [[[[2.3544, 48.8524], [2.3546, 48.8524], [2.3546, 48.8526], [2.3544, 48.8526], [2.3544, 48.8524]]]],
    },
    "properties": {"gid": 10643495, "type": "Bâtiment en dur", "code_dep": "75", "code_insee": "75104"},
}
# a second, unrelated parcel, far from PARCEL_FEATURE and from the test point
PARCEL_FEATURE_FAR = {
    "type": "Feature",
    "geometry": {
        "type": "MultiPolygon",
        "coordinates": [[[[2.360, 48.860], [2.361, 48.860], [2.361, 48.861], [2.360, 48.861], [2.360, 48.860]]]],
    },
    "properties": {
        "idu": "75104000AV0200",
        "section": "AV",
        "numero": "0200",
        "feuille": 1,
        "contenance": 100,
        "nom_com": "Paris 4e Arrondissement",
        "code_insee": "75104",
    },
}

CADASTRAL_BUILDING_OUTSIDE = {
    "type": "Feature",
    "geometry": {
        "type": "MultiPolygon",
        "coordinates": [[[[10.0, 40.0], [10.001, 40.0], [10.001, 40.001], [10.0, 40.001], [10.0, 40.0]]]],
    },
    "properties": {"gid": 999, "type": "Bâtiment en dur", "code_dep": "99", "code_insee": "99999"},
}


class TestGpfChainedGeocoder(unittest.TestCase):
    def test_parcel_with_multiple_buildings_yields_one_result_per_building(self):
        """A parcel with several RNB buildings must produce one
        QgsGeocoderResult per building, not a single result with a list attribute."""
        geocoder = GpfChainedGeocoder()
        geocoder._wfs_client.get_features = lambda *args, **kwargs: []
        geocoder._rnb_geocoder._fetch_rnb_buildings_on_plot = (
            lambda idu: [BUILDING_1, BUILDING_2]
        )
        geocoder._rnb_geocoder._wait_for_rate_limit = lambda feedback=None: False

        results = geocoder._results_for_parcel(
            "75104000AV0117",
            ADDRESS_FIELDS,
            QgsPointXY(2.3545, 48.8525),
            None,
            parcel_feature=PARCEL_FEATURE,
        )

        self.assertEqual(len(results), 2)
        rnb_ids = {result.additionalAttributes()["building_rnb_id"] for result in results}
        self.assertEqual(rnb_ids, {"RBJ8E9C42GDJ", "S65V7NJE3NKS"})
        for result in results:
            attrs = result.additionalAttributes()
            self.assertEqual(attrs["address_label"], ADDRESS_FIELDS["address_label"])
            self.assertEqual(attrs["parcel_idu"], "75104000AV0117")
            self.assertEqual(attrs["parcel_section"], "AV")

    def test_parcel_without_building_yields_one_result_with_no_building(self):
        geocoder = GpfChainedGeocoder()
        geocoder._wfs_client.get_features = lambda *args, **kwargs: []
        geocoder._rnb_geocoder._fetch_rnb_buildings_on_plot = lambda idu: []
        geocoder._rnb_geocoder._wait_for_rate_limit = lambda feedback=None: False

        results = geocoder._results_for_parcel(
            "75104000AV0117",
            ADDRESS_FIELDS,
            QgsPointXY(2.3545, 48.8525),
            None,
            parcel_feature=PARCEL_FEATURE,
        )

        self.assertEqual(len(results), 1)
        attrs = results[0].additionalAttributes()
        self.assertEqual(attrs["parcel_idu"], "75104000AV0117")
        self.assertIsNone(attrs["building_rnb_id"])

    def test_address_only_result_when_no_parcel(self):
        geocoder = GpfChainedGeocoder()
        point = QgsPointXY(2.3545, 48.8525)

        result = geocoder._build_result(ADDRESS_FIELDS, None, None, None, None, point)

        attrs = result.additionalAttributes()
        self.assertEqual(attrs["address_label"], ADDRESS_FIELDS["address_label"])
        self.assertIsNone(attrs["parcel_idu"])
        self.assertIsNone(attrs["building_rnb_id"])
        self.assertIsNone(attrs["building_cadastral_ids"])

    def test_cadastral_building_ids_only_include_intersecting_buildings(self):
        """The PCI 'bâti parcellaire' has no direct key to the parcel, so
        candidates come from a bbox query: only those actually intersecting
        the parcel geometry must end up in building_cadastral_ids."""
        geocoder = GpfChainedGeocoder()

        def fake_get_features(typename, cql_filter=None, bbox=None, count=100, feedback=None):
            if typename == WFS_BATIMENT:
                return [CADASTRAL_BUILDING_INSIDE, CADASTRAL_BUILDING_OUTSIDE]
            return []

        geocoder._wfs_client.get_features = fake_get_features
        geocoder._rnb_geocoder._fetch_rnb_buildings_on_plot = lambda idu: [BUILDING_1]
        geocoder._rnb_geocoder._wait_for_rate_limit = lambda feedback=None: False

        results = geocoder._results_for_parcel(
            "75104000AV0117",
            ADDRESS_FIELDS,
            QgsPointXY(2.3545, 48.8525),
            None,
            parcel_feature=PARCEL_FEATURE,
        )

        self.assertEqual(len(results), 1)
        attrs = results[0].additionalAttributes()
        self.assertEqual(attrs["building_cadastral_ids"], "10643495")

    def test_bdtopo_id_columns_are_independent(self):
        """building_ext_bdtopo_id_wfs (from the WFS lien_bati_parcelle link) and
        building_ext_bdtopo_id_rnb (from the RNB building's own ext_ids) must be
        populated independently, with no fallback/merge between the two."""
        geocoder = GpfChainedGeocoder()
        # no WFS lien_bati_parcelle result at all for this parcel
        geocoder._wfs_client.get_features = lambda *args, **kwargs: []
        geocoder._rnb_geocoder._fetch_rnb_buildings_on_plot = (
            lambda idu: [BUILDING_1, BUILDING_2]
        )
        geocoder._rnb_geocoder._wait_for_rate_limit = lambda feedback=None: False

        results = geocoder._results_for_parcel(
            "75104000AV0117",
            ADDRESS_FIELDS,
            QgsPointXY(2.3545, 48.8525),
            None,
            parcel_feature=PARCEL_FEATURE,
        )

        attrs_by_rnb_id = {
            result.additionalAttributes()["building_rnb_id"]: result.additionalAttributes()
            for result in results
        }
        self.assertIsNone(attrs_by_rnb_id["RBJ8E9C42GDJ"]["building_ext_bdtopo_id_wfs"])
        self.assertEqual(
            attrs_by_rnb_id["RBJ8E9C42GDJ"]["building_ext_bdtopo_id_rnb"],
            "BATIMENT0000000245184192",
        )
        self.assertIsNone(attrs_by_rnb_id["S65V7NJE3NKS"]["building_ext_bdtopo_id_wfs"])
        self.assertIsNone(attrs_by_rnb_id["S65V7NJE3NKS"]["building_ext_bdtopo_id_rnb"])

    def test_select_relevant_parcels_keeps_only_containing_parcel(self):
        """Reverse geocoding must not run the full per-parcel lookup chain
        (3 extra HTTP calls) for every parcel merely inside the search bbox:
        only the parcel actually containing the point should be kept."""
        geocoder = GpfChainedGeocoder()
        point = QgsPointXY(2.3545, 48.8525)  # inside PARCEL_FEATURE only

        selected = geocoder._select_relevant_parcels(
            [PARCEL_FEATURE_FAR, PARCEL_FEATURE], point
        )

        self.assertEqual(len(selected), 1)
        self.assertEqual(selected[0]["properties"]["idu"], "75104000AV0117")

    def test_select_relevant_parcels_falls_back_to_nearest_when_none_contains(self):
        geocoder = GpfChainedGeocoder()
        point = QgsPointXY(0.0, 0.0)  # outside both parcels

        selected = geocoder._select_relevant_parcels(
            [PARCEL_FEATURE, PARCEL_FEATURE_FAR], point
        )

        self.assertEqual(len(selected), 1)
        self.assertEqual(selected[0]["properties"]["idu"], "75104000AV0117")

    def test_parcel_fields_from_feature_stringifies_numeric_properties(self):
        geocoder = GpfChainedGeocoder()

        fields = geocoder._parcel_fields_from_feature(PARCEL_FEATURE, "75104000AV0117")

        self.assertEqual(fields["parcel_idu"], "75104000AV0117")
        self.assertEqual(fields["parcel_section"], "AV")
        self.assertEqual(fields["parcel_numero"], "0117")
        self.assertEqual(fields["parcel_feuille"], "1")
        self.assertEqual(fields["parcel_contenance"], "245")
        self.assertEqual(fields["parcel_commune"], "Paris 4e Arrondissement")

    def test_parcel_fields_fallback_when_feature_missing(self):
        geocoder = GpfChainedGeocoder()

        fields = geocoder._parcel_fields_from_feature(None, "75104000AV0117")

        self.assertEqual(fields["parcel_idu"], "75104000AV0117")
        self.assertIsNone(fields["parcel_section"])

    def test_polygon_wkt_lat_lon_swaps_axes(self):
        """The WFS expects (lat, lon) axis order for CQL_FILTER spatial
        predicates on EPSG:4326 layers (verified live), matching the bbox=
        convention already used elsewhere - not the (lon, lat)/(x, y) order
        QGIS geometries are stored in internally for this CRS."""
        geometry = QgsGeometry.fromWkt(
            "POLYGON((2.354 48.852, 2.355 48.852, 2.355 48.853, 2.354 48.853, 2.354 48.852))"
        )

        wkt = _polygon_wkt_lat_lon(geometry)

        self.assertEqual(
            wkt,
            "MULTIPOLYGON(((48.852 2.354,48.852 2.355,48.853 2.355,"
            "48.853 2.354,48.852 2.354)))",
        )

    def test_polygon_wkt_lat_lon_none_for_non_polygon(self):
        geometry = QgsGeometry.fromPointXY(QgsPointXY(2.3545, 48.8525))

        self.assertIsNone(_polygon_wkt_lat_lon(geometry))


def _make_chained_result(attrs: dict, point: QgsPointXY) -> QgsGeocoderResult:
    """Build a QgsGeocoderResult carrying the given additional attributes,
    as if produced by GpfChainedGeocoder - used to feed build_provenance_layers
    without exercising the full geocodeString/geocodeFeature HTTP chain."""
    geom = QgsGeometry.fromPointXY(point)
    crs = QgsCoordinateReferenceSystem("EPSG:4326")
    result = QgsGeocoderResult("label", geom, crs)
    result.setAdditionalAttributes(attrs)
    return result


BUILDING_1_WITH_SHAPE = dict(BUILDING_1, shape=PARCEL_FEATURE["geometry"])
BUILDING_2_WITH_SHAPE = dict(BUILDING_2, shape=PARCEL_FEATURE["geometry"])


class TestGpfChainedGeocoderProvenanceLayers(unittest.TestCase):
    def _geocoder_with_two_buildings_on_one_parcel(self):
        geocoder = GpfChainedGeocoder()

        def fake_get_features(typename, cql_filter=None, bbox=None, count=100, feedback=None):
            if typename == WFS_PARCELLE:
                return [PARCEL_FEATURE]
            return []

        geocoder._wfs_client.get_features = fake_get_features
        geocoder._rnb_geocoder._wait_for_rate_limit = lambda feedback=None: False
        geocoder._rnb_geocoder.set_last_request_timestamp = lambda ts: None
        geocoder._rnb_geocoder._fetch_rnb_building_detail = {
            "RBJ8E9C42GDJ": BUILDING_1_WITH_SHAPE,
            "S65V7NJE3NKS": BUILDING_2_WITH_SHAPE,
        }.get

        point = QgsPointXY(2.3545, 48.8525)
        geocoder._last_address_points = {
            ADDRESS_FIELDS["address_id"]: QgsGeometry.fromPointXY(point)
        }

        common_attrs = {**ADDRESS_FIELDS, "parcel_idu": "75104000AV0117"}
        row1 = _make_chained_result(
            {**common_attrs, "building_rnb_id": "RBJ8E9C42GDJ"}, point
        )
        row2 = _make_chained_result(
            {**common_attrs, "building_rnb_id": "S65V7NJE3NKS"}, point
        )
        return geocoder, [(1, row1), (2, row2)]

    def test_parcel_is_deduplicated_across_buildings(self):
        """A parcel referenced by 2 rows (one per building) must appear once
        in the "parcel" provenance, not once per row - otherwise the map
        would show the same polygon stacked on itself."""
        geocoder, rows = self._geocoder_with_two_buildings_on_one_parcel()

        entities = geocoder.build_provenance_layers(rows)

        parcels = entities["parcel"]
        self.assertEqual(len(parcels), 1)
        attrs = parcels[0]["attributes"]
        self.assertEqual(attrs["parcel_idu"], "75104000AV0117")
        self.assertEqual(attrs["result_rows"], "1, 2")
        self.assertEqual(attrs["buildings_rnb"], "RBJ8E9C42GDJ, S65V7NJE3NKS")
        self.assertIsNotNone(parcels[0]["geometry"])

    def test_buildings_rnb_are_fetched_individually_with_geometry(self):
        geocoder, rows = self._geocoder_with_two_buildings_on_one_parcel()

        entities = geocoder.build_provenance_layers(rows)

        buildings = {
            entity["attributes"]["building_rnb_id"]: entity
            for entity in entities["building_rnb"]
        }
        self.assertEqual(set(buildings), {"RBJ8E9C42GDJ", "S65V7NJE3NKS"})
        for rnb_id, entity in buildings.items():
            self.assertIsNotNone(entity["geometry"])
            self.assertEqual(entity["attributes"]["parcel_idu"], "75104000AV0117")

    def test_address_is_deduplicated_with_linked_parcels(self):
        geocoder, rows = self._geocoder_with_two_buildings_on_one_parcel()

        entities = geocoder.build_provenance_layers(rows)

        addresses = entities["address"]
        self.assertEqual(len(addresses), 1)
        attrs = addresses[0]["attributes"]
        self.assertEqual(attrs["address_id"], ADDRESS_FIELDS["address_id"])
        self.assertEqual(attrs["parcels"], "75104000AV0117")
        self.assertEqual(attrs["result_rows"], "1, 2")
        self.assertIsNotNone(addresses[0]["geometry"])

    def test_bdtopo_and_pci_layers_empty_without_known_ids(self):
        """No WFS call for BDTOPO/PCI candidates - and thus no entity - when
        a row has neither building_ext_bdtopo_id_* nor building_cadastral_ids."""
        geocoder, rows = self._geocoder_with_two_buildings_on_one_parcel()

        entities = geocoder.build_provenance_layers(rows)

        self.assertEqual(entities["building_bdtopo"], [])
        self.assertEqual(entities["building_pci"], [])


# ############################################################################
# ####### Stand-alone run ########
# ################################
if __name__ == "__main__":
    unittest.main()
