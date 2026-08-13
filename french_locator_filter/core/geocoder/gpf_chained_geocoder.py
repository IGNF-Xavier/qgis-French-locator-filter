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


class GpfChainedGeocoder(GpfRestApiGeocoder):
    """Geocoder chaining address (BAN), building (RNB) and cadastral parcel
    (embedded in the RNB response via ``withPlots=1``) into a single "fiche
    complète" result.

    A building can intersect several parcels (and, in the reverse direction,
    a bounding box can contain several buildings): rather than squeezing a
    variable-length list into one attribute, this geocoder follows the
    pattern already used across the plugin for ambiguous results and returns
    one QgsGeocoderResult per (address, building, parcel) combination - the
    equivalent of a SQL join. Missing legs of the chain (no building found,
    or a building with no parcel) still produce a result, with the
    corresponding fields left as None, instead of being dropped.

    Composes FrenchBanGeocoder and GpfRnbGeocoder rather than reimplementing
    their HTTP/rate-limit logic.
    """

    def __init__(self):
        super().__init__()
        self._address_geocoder = FrenchBanGeocoder()
        self._rnb_geocoder = GpfRnbGeocoder()

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
            "building_rnb_id": QMetaType.Type.QString,
            "building_status": QMetaType.Type.QString,
            "parcel_id": QMetaType.Type.QString,
            "parcel_cover_ratio": QMetaType.Type.QString,
        }

    def maximum_result_for_inverse_geocoding(self) -> int:
        """Maximum result for an inverse geocoding

        :return: maximum result
        :rtype: int
        """
        return 30

    def geocodeString(
        self,
        string: str,
        context: QgsGeocoderContext,
        feedback: Optional[QgsFeedback] = None,
    ) -> List[QgsGeocoderResult]:
        """Geocode a string: resolve the address, then chain to the RNB
        building(s) and parcel(s) at that address.

        Args:
            string (str): search string
            context (QgsGeocoderContext): geocoding context
            feedback (QgsFeedback | None, optional): feedback for geocoding. Defaults to None

        Returns:
            List[QgsGeocoderResult]: list of geocoding results, one per
                (address, building, parcel) combination
        """
        address_results = self._address_geocoder.geocodeString(string, context, feedback)
        if not address_results:
            return []

        best_address = address_results[0]
        address_fields = self._address_fields_from_ban_result(best_address)
        address_point = best_address.geometry().asPoint()

        ban_id = best_address.additionalAttributes().get("id")
        if not ban_id:
            return [
                self._result_from_combo(address_fields, address_point, None, None)
            ]

        if self._rnb_geocoder._wait_for_rate_limit(feedback):
            return []
        try:
            buildings = self._rnb_geocoder._fetch_rnb_buildings(
                f"cle_interop_ban={ban_id}&withPlots=1&format=json"
            )
        finally:
            self._rnb_geocoder.set_last_request_timestamp(
                QDateTime.currentMSecsSinceEpoch()
            )

        return self._combine_results(address_fields, address_point, buildings)

    def geocodeFeature(
        self,
        feature: QgsFeature,
        context: QgsGeocoderContext,
        feedback: Optional[QgsFeedback] = None,
    ) -> List[QgsGeocoderResult]:
        """Geocode a feature: query RNB buildings (with their parcels) in a
        small bounding box around the point. The address is read directly
        from the RNB response (already embedded), no separate BAN call.

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

        if self._rnb_geocoder._wait_for_rate_limit(feedback):
            return []
        try:
            crs = QgsCoordinateReferenceSystem("EPSG:4326")
            rect = self.create_rectangle_around_point(
                crs,
                point,
                self._rnb_geocoder.REVERSE_BBOX_WIDTH_METERS,
                self._rnb_geocoder.REVERSE_BBOX_WIDTH_METERS,
            )
            bbox = (
                f"{rect.xMinimum()},{rect.yMinimum()},"
                f"{rect.xMaximum()},{rect.yMaximum()}"
            )
            buildings = self._rnb_geocoder._fetch_rnb_buildings(
                f"bbox={bbox}&withPlots=1&format=json"
            )
            buildings = self._rnb_geocoder._order_buildings_by_relevance(
                buildings, point
            )
        finally:
            self._rnb_geocoder.set_last_request_timestamp(
                QDateTime.currentMSecsSinceEpoch()
            )

        results = []
        for building in buildings:
            address_fields = self._address_fields_from_building(building)
            coordinates = building.get("point", {}).get("coordinates", [point.x(), point.y()])
            building_point = QgsPointXY(coordinates[0], coordinates[1])
            plots = building.get("plots") or []
            if not plots:
                results.append(
                    self._result_from_combo(
                        address_fields, building_point, building, None
                    )
                )
            else:
                for plot in plots:
                    results.append(
                        self._result_from_combo(
                            address_fields, building_point, building, plot
                        )
                    )
        return results

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

    def _address_fields_from_building(self, building: dict) -> dict:
        """Extract the address_* fields from a RNB building's embedded address

        :param building: RNB building json dict
        :type building: dict
        :return: address fields (address_label, address_id, ...)
        :rtype: dict
        """
        addresses = building.get("addresses") or []
        if not addresses:
            return {name: None for name in self._attributes if name.startswith("address_")}

        address = addresses[0]
        street_part = " ".join(
            part
            for part in [address.get("street_number"), address.get("street")]
            if part
        )
        city_part = " ".join(
            part
            for part in [address.get("city_zipcode"), address.get("city_name")]
            if part
        )
        label = ", ".join(part for part in [street_part, city_part] if part)

        return {
            "address_label": label or None,
            "address_id": address.get("ban_id") or address.get("id"),
            "address_postcode": address.get("city_zipcode"),
            "address_citycode": address.get("city_insee_code"),
            "address_city": address.get("city_name"),
            "address_housenumber": address.get("street_number"),
            "address_street": address.get("street"),
        }

    def _combine_results(
        self, address_fields: dict, address_point: QgsPointXY, buildings: List[dict]
    ) -> List[QgsGeocoderResult]:
        """Fan out an address into one result per (building, parcel) combination

        :param address_fields: address_* fields, already extracted
        :type address_fields: dict
        :param address_point: address point, used as result geometry
        :type address_point: QgsPointXY
        :param buildings: candidate RNB buildings (with "plots" if requested)
        :type buildings: List[dict]
        :return: list of results, at least one (address alone if no building found)
        :rtype: List[QgsGeocoderResult]
        """
        if not buildings:
            return [self._result_from_combo(address_fields, address_point, None, None)]

        results = []
        for building in buildings:
            plots = building.get("plots") or []
            if not plots:
                results.append(
                    self._result_from_combo(address_fields, address_point, building, None)
                )
            else:
                for plot in plots:
                    results.append(
                        self._result_from_combo(
                            address_fields, address_point, building, plot
                        )
                    )
        return results

    def _result_from_combo(
        self,
        address_fields: dict,
        point: QgsPointXY,
        building: Optional[dict],
        plot: Optional[dict],
    ) -> QgsGeocoderResult:
        """Build a QgsGeocoderResult from an (address, building, parcel) combination

        :param address_fields: address_* fields
        :type address_fields: dict
        :param point: result geometry point
        :type point: QgsPointXY
        :param building: RNB building json dict, None if not found
        :type building: Optional[dict]
        :param plot: RNB plot json dict ({"id", "bdg_cover_ratio"}), None if not found
        :type plot: Optional[dict]
        :return: geocoder result
        :rtype: QgsGeocoderResult
        """
        attributes = {name: None for name in self._attributes}
        attributes.update(address_fields)

        label_parts = [address_fields.get("address_label")]

        if building:
            attributes["building_rnb_id"] = building.get("rnb_id")
            attributes["building_status"] = building.get("status")
            label_parts.append(f"Bâtiment {building.get('rnb_id')}")

        if plot:
            attributes["parcel_id"] = plot.get("id")
            attributes["parcel_cover_ratio"] = plot.get("bdg_cover_ratio")
            label_parts.append(f"Parcelle {plot.get('id')}")

        label = " — ".join(part for part in label_parts if part)

        crs = QgsCoordinateReferenceSystem("EPSG:4326")
        geom = QgsGeometry.fromPointXY(point)
        res = QgsGeocoderResult(label, geom, crs)

        viewport = None
        if building:
            shape_geom = self._rnb_geocoder._building_geometry(building)
            if shape_geom:
                viewport = shape_geom.boundingBox()
        if viewport is None:
            viewport = self.create_rectangle_around_point(crs, point, 200, 200)
        res.setViewport(viewport)

        res.setGroup("chained")
        res.setAdditionalAttributes(attributes)
        return res
