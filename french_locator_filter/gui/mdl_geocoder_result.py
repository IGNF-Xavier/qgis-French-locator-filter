# PyQGIS
from qgis.core import QgsFields, QgsGeocoderResult
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
        self._field_names = []

        self.setHorizontalHeaderLabels([self.tr("Nom")])

    def set_fields(self, fields: QgsFields) -> None:
        """(Re)configure the model columns from a geocoder's appended fields
        (one column per field, in addition to the "Nom" column), clearing any
        existing rows.

        :param fields: fields to display as columns (e.g. geocoder.appendedFields())
        :type fields: QgsFields
        """
        self.removeRows(0, self.rowCount())
        self._field_names = [field.name() for field in fields]
        self.setColumnCount(1 + len(self._field_names))
        self.setHorizontalHeaderLabels([self.tr("Nom")] + self._field_names)

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

        additional_attributes = geocoder_result.additionalAttributes()
        for col, field_name in enumerate(self._field_names, start=1):
            self.setData(self.index(row, col), additional_attributes.get(field_name))

    def flags(self, index: QModelIndex):
        """Define flag to disable edition
        :param index: model index
        :type index: QModelIndex
        """
        default_flags = super().flags(index)
        return default_flags & ~Qt.ItemFlag.ItemIsEditable
