#! python3  # noqa E265

"""
Usage from the repo root folder:

.. code-block:: bash

    # for whole tests
    python -m unittest tests.qgis.test_geocodage_capabilities
    # for specific test
    python -m unittest tests.qgis.test_geocodage_capabilities.TestGeocodageCapabilities.test_load_capabilities_bundled
"""

# standard library
import unittest

# project
from french_locator_filter.toolbelt.geocodage_capabilities import (
    bundled_capabilities_path,
    get_index_fields,
    load_capabilities,
)

# ############################################################################
# ########## Classes #############
# ################################


class TestGeocodageCapabilities(unittest.TestCase):
    def test_bundled_capabilities_file_exists(self):
        """The capabilities snapshot committed with the plugin must exist."""
        self.assertTrue(bundled_capabilities_path().exists())

    def test_load_capabilities_bundled(self):
        """Without a user cache, the bundled snapshot must be loaded and expose
        the address, poi and parcel indexes."""
        capabilities = load_capabilities()
        index_ids = [index.get("id") for index in capabilities.get("indexes", [])]

        self.assertIn("address", index_ids)
        self.assertIn("poi", index_ids)
        self.assertIn("parcel", index_ids)

    def test_get_index_fields_known_index(self):
        capabilities = load_capabilities()
        fields = get_index_fields(capabilities, "parcel")
        field_names = [field.get("name") for field in fields]

        self.assertIn("departmentcode", field_names)
        self.assertIn("municipalitycode", field_names)
        self.assertIn("section", field_names)
        self.assertIn("number", field_names)

    def test_get_index_fields_unknown_index(self):
        capabilities = load_capabilities()
        self.assertEqual(get_index_fields(capabilities, "does_not_exist"), [])


# ############################################################################
# ####### Stand-alone run ########
# ################################
if __name__ == "__main__":
    unittest.main()
