import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QPushButton, QLabel, QTabWidget
from PyQt5.QtCore import Qt

from .gsea_res_ploter import GSEAVisualizationGUI
from .gmt_generator import GMTGenerator
from .gsea_runner import EnrichmentApp

class MainGUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("GSEA GUI工具集")
        self.setGeometry(100, 100, 800, 600)
        
        # 创建中央窗口部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 主布局
        main_layout = QVBoxLayout(central_widget)
        
        # 标题标签
        title_label = QLabel("GSEA GUI工具集")
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet("font-size: 20px; font-weight: bold;")
        main_layout.addWidget(title_label)
        
        # 说明标签
        description_label = QLabel("请选择要使用的工具：")
        description_label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(description_label)
        
        # 创建按钮组
        button_layout = QVBoxLayout()
        
        # 富集分析应用按钮
        self.enrichment_app_btn = QPushButton("基因集富集分析")
        self.enrichment_app_btn.setMinimumHeight(50)
        self.enrichment_app_btn.clicked.connect(self.open_enrichment_app)
        button_layout.addWidget(self.enrichment_app_btn)
        
        # GSEA可视化按钮
        self.gsea_vis_btn = QPushButton("GSEA结果可视化")
        self.gsea_vis_btn.setMinimumHeight(50)
        self.gsea_vis_btn.clicked.connect(self.open_gsea_vis)
        button_layout.addWidget(self.gsea_vis_btn)
        
        # GMT生成器按钮
        self.gmt_gen_btn = QPushButton("GMT文件生成器")
        self.gmt_gen_btn.setMinimumHeight(50)
        self.gmt_gen_btn.clicked.connect(self.open_gmt_gen)
        button_layout.addWidget(self.gmt_gen_btn)
        
        main_layout.addLayout(button_layout)
        
        # 版本信息
        version_label = QLabel("版本 0.1.0")
        version_label.setAlignment(Qt.AlignRight)
        main_layout.addWidget(version_label)
        
        # 保存窗口引用
        self.enrichment_app_window = None
        self.gsea_vis_window = None
        self.gmt_gen_window = None
    
    def open_enrichment_app(self):
        """打开基因集富集分析窗口"""
        self.enrichment_app_window = EnrichmentApp()
        self.enrichment_app_window.show()
    
    def open_gsea_vis(self):
        """打开GSEA可视化窗口"""
        self.gsea_vis_window = GSEAVisualizationGUI()
        self.gsea_vis_window.show()
    
    def open_gmt_gen(self):
        """打开GMT生成器窗口"""
        self.gmt_gen_window = GMTGenerator()
        self.gmt_gen_window.show()

def main():
    app = QApplication(sys.argv)
    window = MainGUI()
    window.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
