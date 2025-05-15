from typing import Optional

from qgis import processing
from qgis.core import Qgis, QgsApplication
from qgis.PyQt.QtCore import QObject
from qgis.PyQt.QtWidgets import QAction

from french_locator_filter.toolbelt.log_handler import PlgLogger


def create_processing_action(algorithm_id: str, parent: QObject) -> Optional[QAction]:
    """Create action to display a processing dialog for an algorithm

    :param algorithm_id: algorithm id
    :type algorithm_id: str
    :param parent: parent for QAction
    :type parent: QObject
    :return: QAction connected to processing dialog display, None if processing is not available.
    :rtype: Optional[QAction]
    """
    registry = QgsApplication.processingRegistry()
    alg = registry.algorithmById(algorithm_id)

    if alg is None:
        PlgLogger().log(
            f"Algorithme '{algorithm_id}' non trouvé.",
            log_level=Qgis.MessageLevel.Warning,
        )
        return None

    action = QAction(alg.icon(), alg.displayName(), parent)
    action.setToolTip(alg.shortHelpString())

    action.triggered.connect(lambda: processing.execAlgorithmDialog(algorithm_id))

    return action
