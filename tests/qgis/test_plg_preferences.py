#! python3  # noqa E265

"""
Usage from the repo root folder:

.. code-block:: bash

    # for whole tests
    python -m unittest tests.qgis.test_plg_preferences
    # for specific test
    python -m unittest tests.qgis.test_plg_preferences.TestPlgPreferences.test_plg_preferences_structure
"""

# standard library
import unittest

# project
from french_locator_filter.__about__ import __version__
from french_locator_filter.toolbelt.preferences import PlgSettingsStructure

# ############################################################################
# ########## Classes #############
# ################################


class TestPlgPreferences(unittest.TestCase):
    def test_plg_preferences_structure(self):
        """Test version note named tuple structure and mechanisms."""
        settings = PlgSettingsStructure()

        # global
        self.assertTrue(hasattr(settings, "debug_mode"))
        self.assertIsInstance(settings.debug_mode, bool)
        self.assertEqual(settings.debug_mode, False)

        self.assertTrue(hasattr(settings, "version"))
        self.assertIsInstance(settings.version, str)
        self.assertEqual(settings.version, __version__)

    def test_plg_preferences_search_terms_to_list(self):
        settings = PlgSettingsStructure(search_terms_to_ignore="test, value2")
        self.assertEqual(
            settings.search_terms_to_ignore_list,
            ["test", "value2"],
            "search_terms_to_ignore_list failed",
        )

    def test_plg_preferences_search_terms_to_str(self):
        settings = PlgSettingsStructure(search_terms_to_ignore=("test", "value2"))

        self.assertEqual(settings.terms_to_str, "test, value2", "terms_to_str failed")


# ############################################################################
# ####### Stand-alone run ########
# ################################
if __name__ == "__main__":
    unittest.main()
