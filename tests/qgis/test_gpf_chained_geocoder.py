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
from qgis.core import QgsPointXY

# project
from french_locator_filter.core.geocoder.gpf_chained_geocoder import GpfChainedGeocoder

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

# real building/plots example captured from the RNB API (withPlots=1):
# one building intersecting two cadastral parcels
BUILDING_TWO_PLOTS = {
    "rnb_id": "RSJ5HEMCP3D3",
    "status": "constructed",
    "point": {"type": "Point", "coordinates": [2.354352867209375, 48.85210190224262]},
    "shape": None,
    "addresses": [],
    "plots": [
        {"id": "75104000AV0108", "bdg_cover_ratio": 0.20776904571469965},
        {"id": "75104000AV0109", "bdg_cover_ratio": 0.7712328321391224},
    ],
}

BUILDING_NO_PLOTS = {
    "rnb_id": "TAHJN12ABCDE",
    "status": "constructed",
    "point": {"type": "Point", "coordinates": [2.36, 48.86]},
    "shape": None,
    "addresses": [],
    "plots": [],
}


class TestGpfChainedGeocoder(unittest.TestCase):
    def test_building_with_multiple_plots_yields_one_result_per_plot(self):
        """A building intersecting several parcels must produce one
        QgsGeocoderResult per parcel, not a single result with a list attribute."""
        geocoder = GpfChainedGeocoder()
        point = QgsPointXY(2.354352867209375, 48.85210190224262)

        results = geocoder._combine_results(ADDRESS_FIELDS, point, [BUILDING_TWO_PLOTS])

        self.assertEqual(len(results), 2)
        parcel_ids = {
            result.additionalAttributes()["parcel_id"] for result in results
        }
        self.assertEqual(parcel_ids, {"75104000AV0108", "75104000AV0109"})
        for result in results:
            attrs = result.additionalAttributes()
            self.assertEqual(attrs["address_label"], ADDRESS_FIELDS["address_label"])
            self.assertEqual(attrs["building_rnb_id"], "RSJ5HEMCP3D3")

    def test_building_without_plots_yields_one_result_with_no_parcel(self):
        geocoder = GpfChainedGeocoder()
        point = QgsPointXY(2.36, 48.86)

        results = geocoder._combine_results(ADDRESS_FIELDS, point, [BUILDING_NO_PLOTS])

        self.assertEqual(len(results), 1)
        attrs = results[0].additionalAttributes()
        self.assertEqual(attrs["building_rnb_id"], "TAHJN12ABCDE")
        self.assertIsNone(attrs["parcel_id"])

    def test_no_building_yields_address_only_result(self):
        geocoder = GpfChainedGeocoder()
        point = QgsPointXY(2.354352867209375, 48.85210190224262)

        results = geocoder._combine_results(ADDRESS_FIELDS, point, [])

        self.assertEqual(len(results), 1)
        attrs = results[0].additionalAttributes()
        self.assertEqual(attrs["address_label"], ADDRESS_FIELDS["address_label"])
        self.assertIsNone(attrs["building_rnb_id"])
        self.assertIsNone(attrs["parcel_id"])


# ############################################################################
# ####### Stand-alone run ########
# ################################
if __name__ == "__main__":
    unittest.main()
