"""
gseagui - GUI工具集用于基因集富集分析和可视化
"""

__version__ = '0.1.0'
__author__ = 'Qing'

from .gsea_res_ploter import GSEAVisualizationGUI
from .gmt_generator import GMTGenerator 
from .enrichment_tools import EnrichmentAnalyzer
from .gsea_runner import EnrichmentApp

# 为了方便使用，导出主要类
__all__ = ['GSEAVisualizationGUI', 'GMTGenerator', 'EnrichmentAnalyzer', 'EnrichmentApp']

# 方便的启动函数
def run_enrichment_app():
    """启动富集分析应用程序"""
    import sys
    from PyQt5.QtWidgets import QApplication
    from .gsea_runner import EnrichmentApp
    
    app = QApplication(sys.argv)
    window = EnrichmentApp()
    window.show()
    sys.exit(app.exec_())

def run_visualization_app():
    """启动GSEA可视化应用程序"""
    import sys
    from PyQt5.QtWidgets import QApplication
    from .gsea_res_ploter import GSEAVisualizationGUI
    
    app = QApplication(sys.argv)
    window = GSEAVisualizationGUI()
    window.show()
    sys.exit(app.exec_())

def run_gmt_generator():
    """启动GMT文件生成器"""
    import sys
    from PyQt5.QtWidgets import QApplication
    from .gmt_generator import GMTGenerator
    
    app = QApplication(sys.argv)
    window = GMTGenerator()
    window.show()
    sys.exit(app.exec_())