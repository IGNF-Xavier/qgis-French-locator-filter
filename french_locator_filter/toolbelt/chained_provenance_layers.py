#! python3  # noqa: E265

"""
Build deduplicated per-provenance memory layers (address, parcel, RNB/BDTOPO/PCI
buildings) from a chained geocoder's already-displayed results, so every
geometry involved can be inspected on the map - not just the single result
point. Entities are deduplicated by their natural identifier: a parcel with
several buildings on it is a single feature, not one copy per building.
"""

# standard library
from typing import List, Optional, Tuple

# PyQGIS
from qgis.core import (
    QgsCoordinateReferenceSystem,
    QgsFeature,
    QgsFeedback,
    QgsField,
    QgsFields,
    QgsGeocoderResult,
    QgsProject,
    QgsVectorLayer,
)
from qgis.PyQt.QtCore import QMetaType

# project
from french_locator_filter.core.geocoder.gpf_chained_geocoder import GpfChainedGeocoder

# provenance key (as returned by GpfChainedGeocoder.build_provenance_layers)
# -> (display name, memory layer geometry type)
_PROVENANCE_LAYERS = [
    ("address", "Adresse", "Point"),
    ("parcel", "Parcelle", "MultiPolygon"),
    ("building_rnb", "Bâtiment RNB", "MultiPolygon"),
    ("building_bdtopo", "Bâtiment BDTOPO", "MultiPolygon"),
    ("building_pci", "Bâti PCI", "MultiPolygon"),
]


def add_provenance_layers(
    geocoder: GpfChainedGeocoder,
    rows: List[Tuple[int, QgsGeocoderResult]],
    group_name: str,
    feedback: Optional[QgsFeedback] = None,
) -> List[QgsVectorLayer]:
    """Build the per-provenance memory layers for a chained geocoder's
    displayed results and add them to the project, grouped together.

    :param geocoder: chained geocoder that produced the results
    :type geocoder: GpfChainedGeocoder
    :param rows: (1-based row number, geocoder result) pairs, as displayed
        in the results table
    :type rows: List[Tuple[int, QgsGeocoderResult]]
    :param group_name: name of the layer tree group created to hold the layers
    :type group_name: str
    :param feedback: feedback, defaults to None
    :type feedback: Optional[QgsFeedback]
    :return: the created layers (a provenance with no usable geometry at all
        does not get a layer)
    :rtype: List[QgsVectorLayer]
    """
    entities_by_provenance = geocoder.build_provenance_layers(rows, feedback)

    project = QgsProject.instance()
    group = project.layerTreeRoot().insertGroup(0, group_name)

    layers = []
    for key, display_name, wkb_type in _PROVENANCE_LAYERS:
        layer = _build_layer(entities_by_provenance.get(key, []), display_name, wkb_type)
        if layer is None:
            continue
        project.addMapLayer(layer, addToLegend=False)
        group.addLayer(layer)
        layers.append(layer)

    if not layers:
        project.layerTreeRoot().removeChildNode(group)

    return layers


def _build_layer(
    entities: List[dict], layer_name: str, wkb_type: str
) -> Optional[QgsVectorLayer]:
    """Build a memory layer from a list of {"geometry", "attributes"}
    entities, skipping those without a usable geometry.

    :param entities: entities for one provenance (deduplicated)
    :type entities: List[dict]
    :param layer_name: layer name
    :type layer_name: str
    :param wkb_type: memory provider geometry type ("Point", "MultiPolygon")
    :type wkb_type: str
    :return: the memory layer, None if no entity had a usable geometry
    :rtype: Optional[QgsVectorLayer]
    """
    usable = [entity for entity in entities if entity.get("geometry")]
    if not usable:
        return None

    field_names = list(usable[0]["attributes"].keys())
    fields = QgsFields()
    for name in field_names:
        fields.append(QgsField(name, QMetaType.Type.QString))

    layer = QgsVectorLayer(wkb_type, layer_name, "memory")
    layer.setCrs(QgsCoordinateReferenceSystem("EPSG:4326"))
    provider = layer.dataProvider()
    provider.addAttributes(fields)
    layer.updateFields()

    layer.startEditing()
    for entity in usable:
        feature = QgsFeature(layer.fields())
        feature.setAttributes(
            [entity["attributes"].get(name) for name in field_names]
        )
        feature.setGeometry(entity["geometry"])
        layer.addFeature(feature)
    layer.commitChanges()

    return layer
