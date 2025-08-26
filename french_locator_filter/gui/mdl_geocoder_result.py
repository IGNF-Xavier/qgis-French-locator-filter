# PyQGIS
from qgis.core import QgsGeocoderResult
from qgis.PyQt.QtCore import QModelIndex, QObject, Qt
from qgis.PyQt.QtGui import QStandardItemModel


class QgsGeocoderResultModel(QStandardItemModel):
    IDENTIFIER_COL = 0

    def __init__(self, parent: QObject = None):
        """Constructor

        :param parent: parent, defaults to None
        :type parent: QObject, optional
        """
        super().__init__(0, 1, parent)

        self.setHorizontalHeaderLabels([self.tr("Nom")])

    def add_geocoder_result(self, geocoder_result: QgsGeocoderResult) -> None:
        """Add a geocoder result to model

        :param geocoder_result: geocoder result
        :type geocoder_result: QgsGeocoderResult
        """
        row = self.rowCount()
        self.insertRow(row)
        self.setData(self.index(row, self.IDENTIFIER_COL), geocoder_result.identifier())
        self.setData(
            self.index(row, self.IDENTIFIER_COL),
            geocoder_result,
            Qt.ItemDataRole.UserRole,
        )

    def flags(self, index: QModelIndex):
        """Define flag to disable edition
        :param index: model index
        :type index: QModelIndex
        """
        default_flags = super().flags(index)
        return default_flags & ~Qt.ItemFlag.ItemIsEditable
