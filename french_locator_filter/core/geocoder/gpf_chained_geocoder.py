# standard library
from typing import Dict, List, Optional

# PyQGIS
from qgis.core import (
    Qgis,
    QgsCoordinateReferenceSystem,
    QgsFeature,
    QgsFeedback,
    QgsGeocoderContext,
    QgsGeocoderResult,
    QgsGeometry,
    QgsPointXY,
)
from qgis.PyQt.QtCore import QDateTime, QMetaType

# project
from french_locator_filter.core.geocoder.addok_ban_fr_geocoder import FrenchBanGeocoder
from french_locator_filter.core.geocoder.gpf_rest_api_geocoder import (
    GpfRestApiGeocoder,
)
from french_locator_filter.core.geocoder.gpf_rnb_geocoder import GpfRnbGeocoder
from french_locator_filter.toolbelt.wfs_client import WfsClient

# WFS BAN-PLUS link layers + PCI parcellaire, verified live against
# https://data.geopf.fr/wfs/ows
WFS_LIEN_ADRESSE_PARCELLE = "BAN-PLUS:lien_adresse_parcelle"
WFS_LIEN_BATI_PARCELLE = "BAN-PLUS:lien_bati_parcelle"
WFS_PARCELLE = "CADASTRALPARCELS.PARCELLAIRE_EXPRESS:parcelle"
WFS_BATIMENT = "CADASTRALPARCELS.PARCELLAIRE_EXPRESS:batiment"


def _cql_equals(field: str, value: str) -> str:
    """Build a simple CQL equality filter, escaping single quotes

    :param field: field name
    :type field: str
    :param value: field value
    :type value: str
    :return: CQL filter expression
    :rtype: str
    """
    return f"{field}='{value.replace(chr(39), chr(39) * 2)}'"


class GpfChainedGeocoder(GpfRestApiGeocoder):
    """Geocoder chaining address (BAN), cadastral parcel and RNB building into
    a single "fiche complète" result, using the Géoplateforme WFS BAN-PLUS
    precomputed link layers (address<->parcel, building<->parcel) and the PCI
    "parcellaire express" layer for real parcel geometries, rather than
    reconstructing the link from scratch via RNB bounding-box search.

    A parcel can have several buildings (and an address several parcels):
    rather than squeezing a variable-length list into one attribute, this
    geocoder follows the pattern already used across the plugin for
    ambiguous results and returns one QgsGeocoderResult per (address,
    parcel, building) combination - the equivalent of a SQL join. Missing
    legs of the chain still produce a result, with the corresponding fields
    left as None, instead of being dropped.

    Composes FrenchBanGeocoder and GpfRnbGeocoder rather than reimplementing
    their HTTP/rate-limit logic; uses WfsClient (its own rate limiter) for
    the WFS calls.
    """

    # bounding box half-size (in meters) used around a point for reverse search
    REVERSE_BBOX_WIDTH_METERS = 40

    def __init__(self):
        super().__init__()
        self._address_geocoder = FrenchBanGeocoder()
        self._rnb_geocoder = GpfRnbGeocoder()
        self._wfs_client = WfsClient()

    @property
    def _attributes(self) -> Dict[str, QMetaType.Type]:
        """Get attributes to read from REST API properties.

        Returns:
            Dict[str, QMetaType.Type]: dict of attribute with expected data type
        """
        return {
            "address_label": QMetaType.Type.QString,
            "address_id": QMetaType.Type.QString,
            "address_postcode": QMetaType.Type.QString,
            "address_citycode": QMetaType.Type.QString,
            "address_city": QMetaType.Type.QString,
            "address_housenumber": QMetaType.Type.QString,
            "address_street": QMetaType.Type.QString,
            "parcel_idu": QMetaType.Type.QString,
            "parcel_section": QMetaType.Type.QString,
            "parcel_numero": QMetaType.Type.QString,
            "parcel_feuille": QMetaType.Type.QString,
            "parcel_contenance": QMetaType.Type.QString,
            "parcel_commune": QMetaType.Type.QString,
            "parcel_type_lien": QMetaType.Type.QString,
            "building_rnb_id": QMetaType.Type.QString,
            "building_status": QMetaType.Type.QString,
            "building_ext_bdtopo_id_wfs": QMetaType.Type.QString,
            "building_ext_bdtopo_id_rnb": QMetaType.Type.QString,
            "building_cadastral_ids": QMetaType.Type.QString,
        }

    def maximum_result_for_inverse_geocoding(self) -> int:
        """Maximum result for an inverse geocoding

        :return: maximum result
        :rtype: int
        """
        return 30

    # ------------------------------------------------------------------
    # Direct geocoding: address (BAN) -> parcel(s) (WFS lien_adresse_parcelle)
    # -> building(s) (RNB buildings/plot)
    # ------------------------------------------------------------------

    def geocodeString(
        self,
        string: str,
        context: QgsGeocoderContext,
        feedback: Optional[QgsFeedback] = None,
    ) -> List[QgsGeocoderResult]:
        """Geocode a string: resolve the address, then follow the Géoplateforme
        WFS BAN-PLUS link to the cadastral parcel(s), then to the RNB
        building(s) on each parcel.

        Args:
            string (str): search string
            context (QgsGeocoderContext): geocoding context
            feedback (QgsFeedback | None, optional): feedback for geocoding. Defaults to None

        Returns:
            List[QgsGeocoderResult]: list of geocoding results, one per
                (address, parcel, building) combination
        """
        address_results = self._address_geocoder.geocodeString(string, context, feedback)
        if not address_results:
            return []

        best_address = address_results[0]
        address_fields = self._address_fields_from_ban_result(best_address)
        address_point = best_address.geometry().asPoint()

        id_adr = best_address.additionalAttributes().get("id")
        if not id_adr:
            return [self._build_result(address_fields, None, None, None, None, address_point)]

        parcel_links = self._wfs_client.get_features(
            WFS_LIEN_ADRESSE_PARCELLE,
            cql_filter=_cql_equals("id_adr", id_adr),
            feedback=feedback,
        )
        type_lien_by_idu = {}
        for link in parcel_links:
            props = link.get("properties", {})
            idu = props.get("idu")
            if idu:
                type_lien_by_idu[idu] = props.get("type_lien")

        if not type_lien_by_idu:
            return [self._build_result(address_fields, None, None, None, None, address_point)]

        results = []
        for idu in sorted(type_lien_by_idu):
            results.extend(
                self._results_for_parcel(
                    idu,
                    address_fields,
                    address_point,
                    feedback,
                    type_lien=type_lien_by_idu[idu],
                )
            )
        return results

    # ------------------------------------------------------------------
    # Reverse geocoding: point -> parcel(s) (WFS parcellaire, spatial)
    # -> address (BAN reverse) + building(s) (RNB buildings/plot)
    # ------------------------------------------------------------------

    def geocodeFeature(
        self,
        feature: QgsFeature,
        context: QgsGeocoderContext,
        feedback: Optional[QgsFeedback] = None,
    ) -> List[QgsGeocoderResult]:
        """Geocode a feature: find the cadastral parcel(s) at that point
        directly from the PCI WFS layer, resolve the address at that point
        via BAN reverse geocoding, then the RNB building(s) on each parcel.

        :param feature: input feature, geometry expected in EPSG:4326
        :type feature: QgsFeature
        :param context: geocoder context
        :type context: QgsGeocoderContext
        :param feedback: feedback, defaults to None
        :type feedback: Optional[QgsFeedback]
        :return: list of result for feature
        :rtype: List[QgsGeocoderResult]
        """
        geometry = feature.geometry()
        if not geometry:
            return []

        point = geometry.centroid().asPoint()
        if geometry.type() == Qgis.GeometryType.Point:
            point = geometry.asPoint()

        address_results = self._address_geocoder.geocodeFeature(feature, context, feedback)
        address_fields = (
            self._address_fields_from_ban_result(address_results[0])
            if address_results
            else {name: None for name in self._attributes if name.startswith("address_")}
        )

        crs = QgsCoordinateReferenceSystem("EPSG:4326")
        rect = self.create_rectangle_around_point(
            crs, point, self.REVERSE_BBOX_WIDTH_METERS, self.REVERSE_BBOX_WIDTH_METERS
        )
        bbox = (
            f"{rect.yMinimum()},{rect.xMinimum()},"
            f"{rect.yMaximum()},{rect.xMaximum()},urn:ogc:def:crs:EPSG::4326"
        )
        parcels = self._wfs_client.get_features(
            WFS_PARCELLE, bbox=bbox, feedback=feedback
        )
        parcels = self._order_parcels_by_relevance(parcels, point)

        results = []
        for parcel in parcels:
            idu = parcel.get("properties", {}).get("idu")
            if not idu:
                continue
            results.extend(
                self._results_for_parcel(
                    idu,
                    address_fields,
                    point,
                    feedback,
                    parcel_feature=parcel,
                )
            )
        return results

    # ------------------------------------------------------------------
    # Shared helpers
    # ------------------------------------------------------------------

    def _results_for_parcel(
        self,
        idu: str,
        address_fields: dict,
        fallback_point: QgsPointXY,
        feedback: Optional[QgsFeedback],
        parcel_feature: Optional[dict] = None,
        type_lien: Optional[str] = None,
    ) -> List[QgsGeocoderResult]:
        """Build results for a single cadastral parcel: fetch its real geometry
        (unless already provided), the RNB building(s) on it, and the BDTOPO
        building id(s) linked to it (informational), then fan out one result
        per building found (or a single parcel-only result if none).

        :param idu: cadastral parcel identifier
        :type idu: str
        :param address_fields: address_* fields, already extracted
        :type address_fields: dict
        :param fallback_point: point used as result geometry when neither the
            building nor the parcel provide one
        :type fallback_point: QgsPointXY
        :param feedback: feedback, defaults to None
        :type feedback: Optional[QgsFeedback]
        :param parcel_feature: parcel WFS feature, already fetched (reverse case);
            fetched here if not provided (direct case), defaults to None
        :type parcel_feature: Optional[dict], optional
        :param type_lien: confidence of the address<->parcel WFS link ("BAN"/"GEO"),
            None for reverse geocoding (parcel found spatially, not via the link),
            defaults to None
        :type type_lien: Optional[str], optional
        :return: list of results for this parcel
        :rtype: List[QgsGeocoderResult]
        """
        if parcel_feature is None:
            parcel_features = self._wfs_client.get_features(
                WFS_PARCELLE, cql_filter=_cql_equals("idu", idu), count=1, feedback=feedback
            )
            parcel_feature = parcel_features[0] if parcel_features else None

        parcel_fields = self._parcel_fields_from_feature(parcel_feature, idu)
        parcel_geom = (
            self.geometry_from_geojson(parcel_feature.get("geometry"))
            if parcel_feature
            else None
        )

        bati_links = self._wfs_client.get_features(
            WFS_LIEN_BATI_PARCELLE,
            cql_filter=_cql_equals("idu", idu),
            feedback=feedback,
        )
        ext_bdtopo_ids = ", ".join(
            sorted(
                {
                    link["properties"].get("id_bat")
                    for link in bati_links
                    if link.get("properties", {}).get("id_bat")
                }
            )
        )

        cadastral_ids = ", ".join(
            self._cadastral_building_ids(parcel_geom, feedback)
        )

        if self._rnb_geocoder._wait_for_rate_limit(feedback):
            return []
        try:
            buildings = self._rnb_geocoder._fetch_rnb_buildings_on_plot(idu)
        finally:
            self._rnb_geocoder.set_last_request_timestamp(
                QDateTime.currentMSecsSinceEpoch()
            )

        if not buildings:
            return [
                self._build_result(
                    address_fields,
                    parcel_fields,
                    None,
                    ext_bdtopo_ids or None,
                    cadastral_ids or None,
                    fallback_point,
                    parcel_geom,
                    type_lien=type_lien,
                )
            ]

        return [
            self._build_result(
                address_fields,
                parcel_fields,
                building,
                ext_bdtopo_ids or None,
                cadastral_ids or None,
                fallback_point,
                parcel_geom,
                type_lien=type_lien,
            )
            for building in buildings
        ]

    def _cadastral_building_ids(
        self, parcel_geom: Optional[QgsGeometry], feedback: Optional[QgsFeedback]
    ) -> List[str]:
        """Find the PCI cadastral building(s) ("bâti parcellaire") whose real
        geometry intersects a parcel, and return their `gid` identifiers.

        The PCI `batiment` layer has no direct key to a parcel (unlike
        `lien_bati_parcelle`), so candidates are fetched by bounding box
        around the parcel and then filtered by an actual intersection test.

        :param parcel_geom: parcel real geometry, None if not available
        :type parcel_geom: Optional[QgsGeometry]
        :param feedback: feedback, defaults to None
        :type feedback: Optional[QgsFeedback]
        :return: sorted list of cadastral building gid(s), as strings
        :rtype: List[str]
        """
        if not parcel_geom:
            return []

        rect = parcel_geom.boundingBox()
        bbox = (
            f"{rect.yMinimum()},{rect.xMinimum()},"
            f"{rect.yMaximum()},{rect.xMaximum()},urn:ogc:def:crs:EPSG::4326"
        )
        candidates = self._wfs_client.get_features(
            WFS_BATIMENT, bbox=bbox, feedback=feedback
        )

        gids = set()
        for candidate in candidates:
            candidate_geom = self.geometry_from_geojson(candidate.get("geometry"))
            if candidate_geom and parcel_geom.intersects(candidate_geom):
                gid = candidate.get("properties", {}).get("gid")
                if gid is not None:
                    gids.add(str(gid))
        return sorted(gids)

    def _order_parcels_by_relevance(
        self, parcels: List[dict], point: QgsPointXY
    ) -> List[dict]:
        """Order candidate parcels: those whose polygon contains the point
        first, then all others sorted by distance to the point.

        :param parcels: candidate parcel WFS features
        :type parcels: List[dict]
        :param point: reference point (EPSG:4326)
        :type point: QgsPointXY
        :return: ordered parcels
        :rtype: List[dict]
        """
        point_geom = QgsGeometry.fromPointXY(point)

        def sort_key(parcel: dict):
            geom = self.geometry_from_geojson(parcel.get("geometry"))
            contains = bool(geom and geom.contains(point_geom))
            distance = geom.distance(point_geom) if geom else float("inf")
            return (0 if contains else 1, distance)

        return sorted(parcels, key=sort_key)

    def _address_fields_from_ban_result(self, address_result: QgsGeocoderResult) -> dict:
        """Extract the address_* fields from a FrenchBanGeocoder result

        :param address_result: BAN geocoder result
        :type address_result: QgsGeocoderResult
        :return: address fields (address_label, address_id, ...)
        :rtype: dict
        """
        attrs = address_result.additionalAttributes()
        return {
            "address_label": attrs.get("label"),
            "address_id": attrs.get("id"),
            "address_postcode": attrs.get("postcode"),
            "address_citycode": attrs.get("citycode"),
            "address_city": attrs.get("city"),
            "address_housenumber": attrs.get("housenumber"),
            "address_street": attrs.get("street"),
        }

    def _parcel_fields_from_feature(
        self, parcel_feature: Optional[dict], idu: str
    ) -> dict:
        """Extract the parcel_* fields from a PCI parcelle WFS feature

        :param parcel_feature: parcel WFS feature, None if not found
        :type parcel_feature: Optional[dict]
        :param idu: cadastral parcel identifier (used as fallback)
        :type idu: str
        :return: parcel fields (parcel_idu, parcel_section, ...)
        :rtype: dict
        """
        if not parcel_feature:
            return {
                "parcel_idu": idu,
                "parcel_section": None,
                "parcel_numero": None,
                "parcel_feuille": None,
                "parcel_contenance": None,
                "parcel_commune": None,
            }

        props = parcel_feature.get("properties", {})
        return {
            "parcel_idu": props.get("idu", idu),
            "parcel_section": props.get("section"),
            "parcel_numero": props.get("numero"),
            "parcel_feuille": _str_or_none(props.get("feuille")),
            "parcel_contenance": _str_or_none(props.get("contenance")),
            "parcel_commune": props.get("nom_com"),
        }

    def _bdtopo_id_from_building(self, building: dict) -> Optional[str]:
        """Extract the BDTOPO building id from an RNB building's own `ext_ids`,
        independent of (and not cross-checked against) the WFS `lien_bati_parcelle`
        link, so both sources can be compared side by side.

        :param building: RNB building json dict
        :type building: dict
        :return: BDTOPO id, None if not present in `ext_ids`
        :rtype: Optional[str]
        """
        for ext_id in building.get("ext_ids", []):
            if ext_id.get("source") == "bdtopo":
                return ext_id.get("id")
        return None

    def _build_result(
        self,
        address_fields: dict,
        parcel_fields: Optional[dict],
        building: Optional[dict],
        ext_bdtopo_ids: Optional[str],
        cadastral_ids: Optional[str],
        fallback_point: QgsPointXY,
        parcel_geom: Optional[QgsGeometry] = None,
        type_lien: Optional[str] = None,
    ) -> QgsGeocoderResult:
        """Build a QgsGeocoderResult from an (address, parcel, building) combination

        :param address_fields: address_* fields
        :type address_fields: dict
        :param parcel_fields: parcel_* fields, None if no parcel found
        :type parcel_fields: Optional[dict]
        :param building: RNB building json dict, None if not found
        :type building: Optional[dict]
        :param ext_bdtopo_ids: comma-separated BDTOPO building id(s) linked to
            the parcel via the WFS `lien_bati_parcelle` layer (informational,
            not cross-checked against `building`)
        :type ext_bdtopo_ids: Optional[str]
        :param cadastral_ids: comma-separated PCI cadastral building gid(s)
            intersecting the parcel (informational, not cross-checked against
            `building` or `ext_bdtopo_ids`)
        :type cadastral_ids: Optional[str]
        :param fallback_point: point used as result geometry when neither the
            building nor the parcel provide one
        :type fallback_point: QgsPointXY
        :param parcel_geom: parcel real geometry, already resolved, defaults to None
        :type parcel_geom: Optional[QgsGeometry], optional
        :param type_lien: confidence of the address<->parcel WFS link ("BAN"/"GEO"),
            None for reverse geocoding, defaults to None
        :type type_lien: Optional[str], optional
        :return: geocoder result
        :rtype: QgsGeocoderResult
        """
        attributes = {name: None for name in self._attributes}
        attributes.update(address_fields)

        label_parts = [address_fields.get("address_label")]

        if parcel_fields:
            attributes.update(parcel_fields)
            label_parts.append(f"Parcelle {parcel_fields.get('parcel_idu')}")

        if type_lien:
            attributes["parcel_type_lien"] = type_lien

        if building:
            attributes["building_rnb_id"] = building.get("rnb_id")
            attributes["building_status"] = building.get("status")
            attributes["building_ext_bdtopo_id_rnb"] = self._bdtopo_id_from_building(building)

        if ext_bdtopo_ids:
            attributes["building_ext_bdtopo_id_wfs"] = ext_bdtopo_ids

        if cadastral_ids:
            attributes["building_cadastral_ids"] = cadastral_ids

        label = " — ".join(part for part in label_parts if part)

        crs = QgsCoordinateReferenceSystem("EPSG:4326")

        point = fallback_point
        building_geom = None
        if building:
            building_geom = self.geometry_from_geojson(building.get("shape"))
            coordinates = building.get("point", {}).get("coordinates")
            if coordinates:
                point = QgsPointXY(coordinates[0], coordinates[1])
        elif parcel_geom:
            point = parcel_geom.centroid().asPoint()

        geom = QgsGeometry.fromPointXY(point)
        res = QgsGeocoderResult(label, geom, crs)

        viewport = None
        if parcel_geom:
            viewport = parcel_geom.boundingBox()
        elif building_geom:
            viewport = building_geom.boundingBox()
        if viewport is None:
            viewport = self.create_rectangle_around_point(crs, point, 200, 200)
        res.setViewport(viewport)

        res.setGroup("chained")
        res.setAdditionalAttributes(attributes)
        return res


def _str_or_none(value) -> Optional[str]:
    """Convert a value to str, keeping None as None (used for numeric WFS
    properties stored as QString attributes)"""
    return None if value is None else str(value)
