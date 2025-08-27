"""Widget for reverse geocoding"""

# standard
from pathlib import Path
from typing import Optional

# PyQGIS
from qgis.core import (
    QgsCoordinateReferenceSystem,
    QgsCoordinateTransform,
    QgsCoordinateTransformContext,
    QgsFeature,
    QgsGeocoderContext,
    QgsGeometry,
)
from qgis.PyQt import uic
from qgis.PyQt.QtGui import QColor, QIcon
from qgis.PyQt.QtWidgets import QHeaderView, QWidget

# project
from french_locator_filter.__about__ import DIR_PLUGIN_ROOT
from french_locator_filter.core.geocoder.addok_ban_fr_geocoder import FrenchBanGeocoder
from french_locator_filter.gui.mdl_geocoder_result import QgsGeocoderResultModel


class ReverseGeocodingWidget(QWidget):
    """QWidget to ask geoplateforme for reverse geocoding

    :param parent: dialog parent, defaults to None
    :type parent: Optional[QWidget], optional
    """

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        ui_path = Path(__file__).resolve(True).parent / "wdg_reverse_geocoding.ui"
        uic.loadUi(ui_path, self)

        self.setWindowIcon(
            QIcon(str(DIR_PLUGIN_ROOT / "resources/images/gpf-geocodage.png"))
        )

        self.btn_run.setIcon(QIcon(":images/themes/default/mActionStart.svg"))
        self.btn_run.clicked.connect(self._reverse_geocoding)
        self.wdg_selection.set_marker_color(QColor("green"))

        self.mdl_result = QgsGeocoderResultModel(self)
        self.tbv_geocoder_result.setModel(self.mdl_result)

        self.tbv_geocoder_result.horizontalHeader().setSectionResizeMode(
            0, QHeaderView.ResizeMode.Stretch
        )

    def _reverse_geocoding(self) -> None:
        """Ask for a reverse geocoding"""
        selected_point = self.wdg_selection.get_referenced_displayed_point()

        feature = QgsFeature()
        geometry = QgsGeometry.fromPointXY(selected_point)
        transform_context = QgsCoordinateTransformContext()
        transform = None
        if self.wdg_selection.get_crs() != QgsCoordinateReferenceSystem("EPSG:4326"):
            transform = QgsCoordinateTransform(
                self.wdg_selection.get_crs(),
                QgsCoordinateReferenceSystem("EPSG:4326"),
                transform_context,
            )
            geometry.transform(transform)
        feature.setGeometry(geometry)

        context = QgsGeocoderContext(transform_context)
        geocoder = FrenchBanGeocoder()
        results = geocoder.geocodeFeature(feature, context)

        # Clear current results
        while self.mdl_result.rowCount() != 0:
            self.mdl_result.removeRow(0)

        # Add available results
        for result in results:
            self.mdl_result.add_geocoder_result(result)
