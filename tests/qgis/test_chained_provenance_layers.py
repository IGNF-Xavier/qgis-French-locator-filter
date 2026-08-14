#! python3  # noqa E265

"""
Usage from the repo root folder:

.. code-block:: bash

    # for whole tests
    python -m unittest tests.qgis.test_chained_provenance_layers
"""

# standard library
import unittest

# PyQGIS
from qgis.core import QgsGeometry, QgsPointXY

# project
from french_locator_filter.toolbelt.chained_provenance_layers import _build_layer

# ############################################################################
# ########## Classes #############
# ################################


class TestChainedProvenanceLayers(unittest.TestCase):
    def test_build_layer_skips_entities_without_geometry(self):
        """An entity whose geometry could not be resolved (e.g. an RNB
        building with no shape) must be left out of the layer rather than
        crash feature creation - only entities with a usable geometry end
        up on the map."""
        entities = [
            {
                "geometry": QgsGeometry.fromPointXY(QgsPointXY(2.3545, 48.8525)),
                "attributes": {"address_id": "75104_5599_00007", "result_rows": "1"},
            },
            {"geometry": None, "attributes": {"address_id": "unresolved", "result_rows": "2"}},
        ]

        layer = _build_layer(entities, "Adresse", "Point")

        self.assertIsNotNone(layer)
        self.assertEqual(layer.featureCount(), 1)
        feature = next(layer.getFeatures())
        self.assertEqual(feature["address_id"], "75104_5599_00007")
        self.assertEqual(feature["result_rows"], "1")

    def test_build_layer_none_when_no_entity_has_geometry(self):
        entities = [{"geometry": None, "attributes": {"address_id": "unresolved"}}]

        layer = _build_layer(entities, "Adresse", "Point")

        self.assertIsNone(layer)

    def test_build_layer_empty_list_returns_none(self):
        self.assertIsNone(_build_layer([], "Adresse", "Point"))


# ############################################################################
# ####### Stand-alone run ########
# ################################
if __name__ == "__main__":
    unittest.main()
