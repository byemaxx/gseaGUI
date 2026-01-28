"""gseagui - GUI工具集用于基因集富集分析和可视化"""

from __future__ import annotations

from importlib.metadata import PackageNotFoundError, version
from pathlib import Path
import re
from typing import TYPE_CHECKING, Any

__author__ = "Qing"


def _version_from_pyproject() -> str | None:
    pyproject_path = Path(__file__).resolve().parents[1] / "pyproject.toml"
    if not pyproject_path.exists():
        return None
    text = pyproject_path.read_text(encoding="utf-8")
    project_match = re.search(r"(?ms)^\[project\]\s*$(.*?)(^\[|\Z)", text)
    if not project_match:
        return None
    project_block = project_match.group(1)
    version_match = re.search(r"(?m)^version\s*=\s*\"([^\"]+)\"\s*$", project_block)
    if not version_match:
        return None
    return version_match.group(1)


_source_version = _version_from_pyproject()
if _source_version:
    __version__ = _source_version
else:
    try:
        __version__ = version("gseagui")
    except PackageNotFoundError:
        __version__ = "0.0.0"

# 为了方便使用，导出主要类（延迟导入，避免打包/启动时因为子模块缺失导致整个包导入失败）
__all__ = [
    "GSEAVisualizationGUI",
    "GMTGenerator",
    "EnrichmentAnalyzer",
    "EnrichmentApp",
]

if TYPE_CHECKING:
    from .enrichment_tools import EnrichmentAnalyzer as EnrichmentAnalyzer
    from .gsea_res_ploter import GSEAVisualizationGUI as GSEAVisualizationGUI
    from .gsea_runner import EnrichmentApp as EnrichmentApp
    from .gmt_generator import GMTGenerator as GMTGenerator


def __getattr__(name: str) -> Any:
    if name == "GSEAVisualizationGUI":
        from .gsea_res_ploter import GSEAVisualizationGUI

        return GSEAVisualizationGUI
    if name == "GMTGenerator":
        from .gmt_generator import GMTGenerator

        return GMTGenerator
    if name == "EnrichmentAnalyzer":
        from .enrichment_tools import EnrichmentAnalyzer

        return EnrichmentAnalyzer
    if name == "EnrichmentApp":
        from .gsea_runner import EnrichmentApp

        return EnrichmentApp
    raise AttributeError(name)

# 方便的启动函数
def run_enrichment_app():
    """启动富集分析应用程序"""
    import sys
    from PyQt5.QtWidgets import QApplication
    from .gsea_runner import EnrichmentApp
    from .qt_utils import apply_application_ui_scale, set_qt_highdpi_attributes
    
    set_qt_highdpi_attributes()
    app = QApplication(sys.argv)
    apply_application_ui_scale(app)
    window = EnrichmentApp()
    window.show()
    sys.exit(app.exec_())

def run_visualization_app():
    """启动GSEA可视化应用程序"""
    import sys
    from PyQt5.QtWidgets import QApplication
    from .gsea_res_ploter import GSEAVisualizationGUI
    from .qt_utils import apply_application_ui_scale, set_qt_highdpi_attributes
    
    set_qt_highdpi_attributes()
    app = QApplication(sys.argv)
    apply_application_ui_scale(app)
    window = GSEAVisualizationGUI()
    window.show()
    sys.exit(app.exec_())

def run_gmt_generator():
    """启动GMT文件生成器"""
    import sys
    from PyQt5.QtWidgets import QApplication
    from .gmt_generator import GMTGenerator
    from .qt_utils import apply_application_ui_scale, set_qt_highdpi_attributes
    
    set_qt_highdpi_attributes()
    app = QApplication(sys.argv)
    apply_application_ui_scale(app)
    window = GMTGenerator()
    window.show()
    sys.exit(app.exec_())