import os
from pathlib import Path
from typing import Optional

# PyQgis
from qgis import processing
from qgis.core import Qgis, QgsApplication, QgsSettings
from qgis.PyQt.QtCore import QObject
from qgis.PyQt.QtWidgets import QAction

# project
from french_locator_filter.__about__ import __uri_homepage__
from french_locator_filter.toolbelt.log_handler import PlgLogger


def get_locale_prefix() -> str:
    """Return prefix to used for localized help

    :return: locale prefix
    :rtype: str
    """
    settings = QgsSettings()
    locale = settings.value("locale/userLocale", "en")
    if locale.startswith("fr"):
        return "fr_"
    return "en_"


def get_user_manual_url(processing_name: str) -> str:
    """Return url to user manual for a processing

    :param processing_name: processing name
    :type processing_name: str
    :return: user manual url
    :rtype: str
    """
    return f"{__uri_homepage__}/usage/{get_locale_prefix()}processings.html#{processing_name}"


def get_short_string(processing_name: str, default_help_str: str) -> str:
    """Get short string help for a processing.
    Use value defined in ../resources/help/locale_prefixe_processing_name.md if available.
    Otherwise, default_help_str is used

    :param processing_name: processing name
    :type processing_name: str
    :param default_help_str: default help string if no value available
    :type default_help_str: str
    :return: processing short string help
    :rtype: str
    """
    current_dir = Path(os.path.dirname(os.path.realpath(__file__)))
    help_md = (
        current_dir
        / ".."
        / "resources"
        / "help"
        / f"{get_locale_prefix()}{processing_name}.md"
    )
    help_str = default_help_str
    if os.path.exists(help_md):
        with open(help_md) as f:
            help_str = "".join(f.readlines())
    return help_str


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
