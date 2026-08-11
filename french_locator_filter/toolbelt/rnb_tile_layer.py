#! python3  # noqa: E265

"""
Helper to add the RNB (Référentiel National du Bâti) vector tile layer to
the current project, so reverse-geocoding results can be visually checked
against real building footprints.
"""

# standard library
from typing import Optional
from urllib.parse import quote

# PyQGIS
from qgis.core import QgsProject, QgsVectorTileLayer

RNB_TILE_LAYER_URL = (
    "https://rnb-api.beta.gouv.fr/api/alpha/tiles/shapes/{x}/{y}/{z}.pbf"
)
RNB_TILE_LAYER_NAME = "RNB - Bâtiments (tuiles vectorielles)"
RNB_TILE_LAYER_MIN_ZOOM = 16
RNB_TILE_LAYER_MAX_ZOOM = 20
RNB_TILE_LAYER_CUSTOM_PROPERTY = "french_locator_filter/rnb_tile_layer"


def add_rnb_vector_tile_layer() -> Optional[QgsVectorTileLayer]:
    """Add the RNB buildings vector tile layer to the current project, reusing
    the existing one if it was already added.

    :return: the added (or existing) layer, None if it could not be created
    :rtype: Optional[QgsVectorTileLayer]
    """
    project = QgsProject.instance()
    for layer in project.mapLayers().values():
        if layer.customProperty(RNB_TILE_LAYER_CUSTOM_PROPERTY):
            return layer

    encoded_url = quote(RNB_TILE_LAYER_URL, safe=":/")
    uri = (
        f"type=xyz&url={encoded_url}"
        f"&zmax={RNB_TILE_LAYER_MAX_ZOOM}&zmin={RNB_TILE_LAYER_MIN_ZOOM}"
    )
    layer = QgsVectorTileLayer(uri, RNB_TILE_LAYER_NAME)
    if not layer.isValid():
        return None

    layer.setCustomProperty(RNB_TILE_LAYER_CUSTOM_PROPERTY, True)
    project.addMapLayer(layer)
    return layer
