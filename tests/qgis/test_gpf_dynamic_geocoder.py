#! python3  # noqa E265

"""
Usage from the repo root folder:

.. code-block:: bash

    # for whole tests
    python -m unittest tests.qgis.test_gpf_dynamic_geocoder
"""

# standard library
import unittest

# project
from french_locator_filter.core.geocoder.gpf_dynamic_geocoder import GpfDynamicGeocoder

# ############################################################################
# ########## Classes #############
# ################################

ADDRESS_RESPONSE = {
    "type": "Feature",
    "geometry": {"type": "Point", "coordinates": [2.354, 48.852]},
    "properties": {
        "_type": "address",
        "label": "10 Rue de Rivoli 75004 Paris",
        "id": "75104_1234_00010",
        "city": "Paris",
        "postcode": "75004",
    },
}

POI_RESPONSE = {
    "type": "Feature",
    "geometry": {"type": "Point", "coordinates": [2.36, 48.86]},
    "properties": {
        "_type": "poi",
        "toponym": "Pont National",
        "category": ["construction linéaire"],
        "postcode": [77310, 91100],
        "city": ["Saint-Fargeau-Ponthierry", "Corbeil-Essonnes"],
    },
}

PARCEL_RESPONSE = {
    "type": "Feature",
    "geometry": {"type": "Point", "coordinates": [2.35461, 48.85234]},
    "properties": {
        "_type": "parcel",
        "id": "75056104AV0133",
        "departmentcode": "75",
        "municipalitycode": "056",
        "city": "Paris",
        "section": "AV",
        "number": "133",
    },
}


class TestGpfDynamicGeocoder(unittest.TestCase):
    def test_attributes_union_multiple_indexes(self):
        """When several indexes are active, appended fields must be the union of
        each index's fields (address + poi here)."""
        geocoder = GpfDynamicGeocoder()
        geocoder.plg_settings.request_indexes = "address,poi"

        attribute_names = list(geocoder._attributes.keys())

        # address-only fields
        self.assertIn("housenumber", attribute_names)
        self.assertIn("citycode", attribute_names)
        # poi-only fields
        self.assertIn("toponyme", attribute_names)
        self.assertIn("category", attribute_names)

    def test_result_from_json_address(self):
        geocoder = GpfDynamicGeocoder()
        geocoder.plg_settings.request_indexes = "address"

        result = geocoder._result_from_json(ADDRESS_RESPONSE)

        self.assertEqual(result.identifier(), "10 Rue de Rivoli 75004 Paris")
        self.assertEqual(result.group(), "address")

    def test_result_from_json_poi_uses_toponym_override(self):
        """The capabilities describe the field as "toponyme" but the actual API
        response uses "toponym": the override mapping must bridge the two, and
        list-valued properties must be flattened to a comma-separated string."""
        geocoder = GpfDynamicGeocoder()
        geocoder.plg_settings.request_indexes = "poi"

        result = geocoder._result_from_json(POI_RESPONSE)

        self.assertEqual(result.identifier(), "Pont National")
        self.assertEqual(result.group(), "poi")
        additional_attributes = result.additionalAttributes()
        self.assertEqual(additional_attributes["toponyme"], "Pont National")
        self.assertEqual(
            additional_attributes["city"],
            "Saint-Fargeau-Ponthierry, Corbeil-Essonnes",
        )

    def test_result_from_json_poi_label_fallback_to_category(self):
        geocoder = GpfDynamicGeocoder()
        geocoder.plg_settings.request_indexes = "poi"

        response = {
            "type": "Feature",
            "geometry": {"type": "Point", "coordinates": [2.36, 48.86]},
            "properties": {"_type": "poi", "category": ["cimetière"]},
        }
        result = geocoder._result_from_json(response)

        self.assertEqual(result.identifier(), "cimetière")

    def test_result_from_json_parcel(self):
        geocoder = GpfDynamicGeocoder()
        geocoder.plg_settings.request_indexes = "parcel"

        result = geocoder._result_from_json(PARCEL_RESPONSE)

        self.assertEqual(result.identifier(), "133 AV - Paris (75056)")
        self.assertEqual(result.group(), "parcel")

    def test_result_from_json_parcel_has_result_index(self):
        """Parcel (and POI) results have no "type" property unlike address
        results: result_index must still be populated, from "_type", so the
        row is identifiable regardless of which index produced it."""
        geocoder = GpfDynamicGeocoder()
        geocoder.plg_settings.request_indexes = "parcel"

        result = geocoder._result_from_json(PARCEL_RESPONSE)

        self.assertEqual(result.additionalAttributes()["result_index"], "parcel")


# ############################################################################
# ####### Stand-alone run ########
# ################################
if __name__ == "__main__":
    unittest.main()
