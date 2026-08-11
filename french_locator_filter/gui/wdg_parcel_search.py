"""Widget for structured parcel search (department -> commune -> section -> number)"""

# standard library
import json
from pathlib import Path
from typing import Optional

# PyQGIS
from qgis.core import Qgis
from qgis.PyQt import uic
from qgis.PyQt.QtCore import Qt
from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtWidgets import QHeaderView, QWidget

# project
from french_locator_filter.__about__ import DIR_PLUGIN_ROOT
from french_locator_filter.core.geocoder.gpf_parcel_geocoder import GpfParcelGeocoder
from french_locator_filter.gui.mdl_geocoder_result import QgsGeocoderResultModel
from french_locator_filter.toolbelt.french_departments import FRENCH_DEPARTMENTS
from french_locator_filter.toolbelt.geocoder_result_layer import add_results_as_layer
from french_locator_filter.toolbelt.log_handler import PlgLogger
from french_locator_filter.toolbelt.network_manager import NetworkRequestsManager

COMMUNES_API_URL = "https://geo.api.gouv.fr/communes"


class ParcelSearchWidget(QWidget):
    """QWidget to search cadastral parcels using structured filters (Géoplateforme
    parcel index): department, commune, section, number.

    :param parent: dialog parent, defaults to None
    :type parent: Optional[QWidget], optional
    """

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.log = PlgLogger().log
        ui_path = Path(__file__).resolve(True).parent / "wdg_parcel_search.ui"
        uic.loadUi(ui_path, self)

        self.setWindowIcon(
            QIcon(str(DIR_PLUGIN_ROOT / "resources/images/gpf-geocodage.png"))
        )

        self._geocoder = GpfParcelGeocoder()

        self.mdl_result = QgsGeocoderResultModel(self)
        self.tbv_geocoder_result.setModel(self.mdl_result)
        self.tbv_geocoder_result.horizontalHeader().setSectionResizeMode(
            0, QHeaderView.ResizeMode.Stretch
        )

        for code, name in FRENCH_DEPARTMENTS:
            self.cbx_department.addItem(f"{code} - {name}", code)

        self.cbx_department.currentIndexChanged.connect(self._on_department_changed)
        self.btn_search.clicked.connect(self._search_parcel)
        self.btn_load.setIcon(QIcon(":/images/themes/default/mActionCreateMemory.svg"))
        self.btn_load.clicked.connect(self._load_results)

        self._on_department_changed()

    def _on_department_changed(self) -> None:
        """Refresh the commune combo box with communes of the selected department"""
        self.cbx_commune.clear()
        departmentcode = self.cbx_department.currentData()
        if not departmentcode:
            return

        try:
            qntwk = NetworkRequestsManager()
            qurl = qntwk.build_url(
                request_url=COMMUNES_API_URL,
                request_url_query=(
                    f"codeDepartement={departmentcode}&fields=nom,code&format=json"
                ),
            )
            response_content = qntwk.get_url(url=qurl)
            communes = json.loads(str(response_content, "UTF8"))
            for commune in sorted(communes, key=lambda c: c.get("nom", "")):
                # the parcel index expects the municipality code without its
                # department prefix (e.g. INSEE 28019 -> municipalitycode "019")
                municipalitycode = commune["code"][len(departmentcode) :]
                self.cbx_commune.addItem(
                    f"{commune['nom']} ({commune['code']})", municipalitycode
                )
        except Exception as err:
            self.log(
                message=self.tr(
                    "Impossible de récupérer la liste des communes : {}".format(err)
                ),
                log_level=Qgis.MessageLevel.Warning,
            )

    def _search_parcel(self) -> None:
        """Search parcels using the current structured filters"""
        departmentcode = self.cbx_department.currentData()
        municipalitycode = self.cbx_commune.currentData()
        if not departmentcode or not municipalitycode:
            return

        section = self.lne_section.text().strip() or None
        number = self.lne_number.text().strip() or None

        results = self._geocoder.search_structured(
            departmentcode=departmentcode,
            municipalitycode=municipalitycode,
            section=section,
            number=number,
        )

        while self.mdl_result.rowCount() != 0:
            self.mdl_result.removeRow(0)

        for result in results:
            self.mdl_result.add_geocoder_result(result)

    def _load_results(self) -> None:
        """Load result as QgsVectorLayer from current search"""
        results = []
        for row in range(0, self.mdl_result.rowCount()):
            geocoder_result = self.mdl_result.data(
                self.mdl_result.index(row, self.mdl_result.IDENTIFIER_COL),
                Qt.ItemDataRole.UserRole,
            )
            if geocoder_result:
                results.append(geocoder_result)

        add_results_as_layer(
            self._geocoder, results, self.tr("Résultats recherche de parcelle")
        )
