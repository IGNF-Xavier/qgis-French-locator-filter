"""Widget to select point on canvas for a specified CRS"""

# standard
from pathlib import Path
from typing import Optional, Union

# PyQGIS
from qgis.core import (
    Qgis,
    QgsCoordinateReferenceSystem,
    QgsCoordinateTransform,
    QgsPointXY,
    QgsRectangle,
    QgsReferencedPointXY,
)
from qgis.gui import (
    QgsMapTool,
    QgsMapToolEmitPoint,
    QgsProjectionSelectionDialog,
    QgsVertexMarker,
)
from qgis.PyQt import uic
from qgis.PyQt.QtCore import Qt
from qgis.PyQt.QtGui import QColor, QIcon
from qgis.PyQt.QtWidgets import QWidget
from qgis.utils import iface


class PointSelectionWidget(QWidget):
    """Widget to select point on canvas for a specified CRS

    :param parent: dialog parent, defaults to None
    :type parent: Optional[QWidget], optional
    """

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        ui_path = Path(__file__).resolve(True).parent / "wdg_point_selection.ui"
        uic.loadUi(ui_path, self)

        # Add marker for selected point
        self.marker = QgsVertexMarker(iface.mapCanvas())
        self.marker.setColor(QColor("red"))
        self.marker.setIconType(QgsVertexMarker.IconType.ICON_CROSS)
        self.marker.setIconSize(12)
        self.marker.setPenWidth(3)

        # Not visible until maptool is activated
        self.marker.setVisible(False)

        self.btn_show_point.setChecked(False)
        self.btn_show_point.setToolTip(self.tr("Visibilité marqueur"))
        self.btn_show_point.setIcon(
            QIcon(":images/themes/default/mActionShowAllLayersGray.svg")
        )
        self.btn_show_point.clicked.connect(self._show_point_clicked)

        # Connect to value changes for marker coordinate update
        self.spb_x.valueChanged.connect(self._update_marker_position)
        self.spb_y.valueChanged.connect(self._update_marker_position)

        # By default use current mapCanvas destination Crs
        self._current_crs = iface.mapCanvas().mapSettings().destinationCrs()
        self.set_crs(self._current_crs)

        # Create maptool for position selection
        self._previous_map_tool = None
        self._map_tool = QgsMapToolEmitPoint(iface.mapCanvas())
        self._map_tool.canvasClicked.connect(self._point_selected)

        self.btn_select_point.setToolTip(self.tr("Sélection point"))
        self.btn_select_point.setIcon(
            QIcon(":images/themes/default/cursors/mCapturePoint.svg")
        )
        self.btn_select_point.clicked.connect(self._selection_clicked)

        self.btn_projection.setToolTip(self.tr("Sélection projection"))
        self.btn_projection.setIcon(
            QIcon(":images/themes/default/propertyicons/CRS.svg")
        )
        self.btn_projection.clicked.connect(self._select_crs)

        iface.mapCanvas().mapToolSet.connect(self._canvas_maptool_set)

    def get_displayed_point(self) -> QgsPointXY:
        """Return displayed point

        :return: displayed point
        :rtype: QgsPointXY
        """
        return QgsPointXY(self.spb_x.value(), self.spb_y.value())

    def set_marker_color(self, color: QColor) -> None:
        """Define color used for marker

        :param color: _description_
        :type color: QColor
        """
        self.marker.setColor(color)

    def get_referenced_displayed_point(self) -> QgsReferencedPointXY:
        """Return display point with associated crs

        :return: display point with associated crs
        :rtype: QgsReferencedPointXY
        """
        return QgsReferencedPointXY(self.get_displayed_point(), self.get_crs())

    def set_display_point(self, point: QgsPointXY) -> None:
        """Define display point and update marker

        :param point: point to display
        :type point: QgsPointXY
        """

        self.spb_x.valueChanged.disconnect(self._update_marker_position)
        self.spb_y.valueChanged.disconnect(self._update_marker_position)

        self.spb_x.setValue(point.x())
        self.spb_y.setValue(point.y())

        self.spb_x.valueChanged.connect(self._update_marker_position)
        self.spb_y.valueChanged.connect(self._update_marker_position)

        self._update_marker_position()

    def _update_marker_position(self) -> None:
        """Update marker with new point values"""
        point = self.get_displayed_point()
        new_point = self._transform(
            point, self._current_crs, iface.mapCanvas().mapSettings().destinationCrs()
        )
        self.marker.setCenter(new_point)

    def _show_point_clicked(self, checked: bool) -> None:
        """Update icon for show point button and marker visibility

        :param checked: True if show point button is checked, False otherwise
        :type checked: bool
        """
        self.marker.setVisible(checked)
        if checked:
            self.btn_show_point.setIcon(
                QIcon(":images/themes/default/mActionShowAllLayers.svg")
            )
        else:
            self.btn_show_point.setIcon(
                QIcon(":images/themes/default/mActionShowAllLayersGray.svg")
            )

    def _canvas_maptool_set(self, tool: QgsMapTool) -> None:
        """Update selection button when maptool is updated

        :param tool: new maptool
        :type tool: QgsMapTool
        """
        if tool != self._map_tool:
            self._previous_map_tool = tool

            self.btn_select_point.clicked.disconnect(self._selection_clicked)
            self.btn_select_point.setChecked(False)
            self.btn_select_point.clicked.connect(self._selection_clicked)

            self.btn_show_point.setEnabled(True)

    def get_crs(self) -> QgsCoordinateReferenceSystem:
        """Get crs

        :return: crs used
        :rtype: QgsCoordinateReferenceSystem
        """
        return self._current_crs

    def set_crs(self, crs: QgsCoordinateReferenceSystem) -> None:
        """Define crs used, current displayed point is transformed

        :param crs: new crs
        :type crs: QgsCoordinateReferenceSystem
        """
        # Update point with new crs
        new_point = self._transform(self.get_displayed_point(), self._current_crs, crs)

        # Update spinbox min/max value
        self._update_spinbox_for_crs(crs)

        # Store used crs, need to be done before point display for marker coordinate transform
        self._current_crs = crs

        # Display projected point
        self.set_display_point(new_point)

    def _select_crs(self):
        """Select new crs"""
        selector = QgsProjectionSelectionDialog(iface.mainWindow())
        selector.setCrs(self._current_crs)
        if selector.exec():
            self.set_crs(selector.crs())

    def _update_spinbox_for_crs(self, crs: QgsCoordinateReferenceSystem) -> None:
        """Update X,Y spinbox with crs bounds

        :param crs: crs
        :type crs: QgsCoordinateReferenceSystem
        """
        bounds = crs.bounds()

        # CRS bounds are always defined in EPSG:4362, convert for X,Y min and max value
        bounds = self._transform(
            crs.bounds(), QgsCoordinateReferenceSystem("EPSG:4326"), crs
        )

        self.spb_x.valueChanged.disconnect(self._update_marker_position)
        self.spb_y.valueChanged.disconnect(self._update_marker_position)

        self.spb_x.setMinimum(bounds.xMinimum())
        self.spb_x.setMaximum(bounds.xMaximum())
        self.spb_y.setMinimum(bounds.yMinimum())
        self.spb_y.setMaximum(bounds.yMaximum())

        if crs.mapUnits() == Qgis.DistanceUnit.Degrees:
            decimal = 5
            step = 0.1
        else:
            decimal = 3
            step = 10

        self.spb_x.setDecimals(decimal)
        self.spb_x.setSingleStep(step)
        self.spb_y.setDecimals(decimal)
        self.spb_y.setSingleStep(step)

        self.spb_x.valueChanged.connect(self._update_marker_position)
        self.spb_y.valueChanged.connect(self._update_marker_position)

    def _selection_clicked(self) -> None:
        """Update maptool used and display marker if activated"""
        if self.btn_select_point.isChecked():
            # Keep previous map tool to be able to restore it
            self._previous_map_tool = iface.mapCanvas().mapTool()

            iface.mapCanvas().setMapTool(self._map_tool)
            self._map_tool.activate()

            self._update_marker_position()
            self.btn_show_point.setChecked(True)
            self.btn_show_point.setEnabled(False)
            self._show_point_clicked(True)
        else:
            self.btn_show_point.setEnabled(True)
            self._map_tool.deactivate()
            # Restore previous map tool if available
            if self._previous_map_tool:
                iface.mapCanvas().setMapTool(self._previous_map_tool)

    def _point_selected(self, point: QgsPointXY, button: Qt.MouseButton) -> None:
        """Update displayed point after selection

        :param point: selected point
        :type point: QgsPointXY
        :param button: button used for selection (unused)
        :type button: Qt.MouseButton
        """
        # Update point with wanted crs
        new_point = self._transform(
            point, iface.mapCanvas().mapSettings().destinationCrs(), self._current_crs
        )
        self.set_display_point(new_point)

    @staticmethod
    def _transform(
        geom: Union[QgsPointXY, QgsRectangle],
        src: QgsCoordinateReferenceSystem,
        dest: QgsCoordinateReferenceSystem,
    ) -> Union[QgsPointXY, QgsRectangle]:
        """Transform geometry from a source CRS to a destination CRS

        :param geom: input geom
        :type geom: Union[QgsPointXY, QgsRectangle]
        :param src: source crs
        :type src: QgsCoordinateReferenceSystem
        :param dest: destination crs
        :type dest: QgsCoordinateReferenceSystem
        :return: transformed geometry
        :rtype: Union[QgsPointXY, QgsRectangle]
        """
        transform = QgsCoordinateTransform()
        transform.setSourceCrs(src)
        transform.setDestinationCrs(dest)
        return transform.transform(geom)
