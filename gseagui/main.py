import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QPushButton, QLabel, QComboBox, QHBoxLayout
from PyQt5.QtCore import Qt

try:
    from gseagui.qt_utils import apply_application_ui_scale, set_qt_highdpi_attributes
except ImportError:
    from qt_utils import apply_application_ui_scale, set_qt_highdpi_attributes

try:
    from gseagui.gsea_res_ploter import GSEAVisualizationGUI
    from gseagui.gmt_generator import GMTGenerator
    from gseagui.gsea_runner import EnrichmentApp
    from gseagui.translations import TRANSLATIONS
    from gseagui import __version__ as APP_VERSION
except ImportError:
    # 打包成 exe（sys.frozen=True）时不应走本地脚本导入分支，否则会把真实错误掩盖掉。
    if getattr(sys, "frozen", False):
        raise
    from gsea_res_ploter import GSEAVisualizationGUI
    from gmt_generator import GMTGenerator
    from gsea_runner import EnrichmentApp
    from translations import TRANSLATIONS
    from __init__ import __version__ as APP_VERSION

class MainGUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.current_lang = "en"  # Default to English
        
        self.setWindowTitle(TRANSLATIONS["main"][self.current_lang]["window_title"])
        
        # Set window size
        self.resize(400, 400)
        
        # Center the window on screen
        self.center()
        
        # Create central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main layout
        main_layout = QVBoxLayout(central_widget)
        
        # Language selection layout (Top Right)
        lang_layout = QHBoxLayout()
        lang_layout.addStretch()
        
        self.lang_combo = QComboBox()
        self.lang_combo.addItem("English", "en")
        self.lang_combo.addItem("中文", "zh")
        self.lang_combo.currentIndexChanged.connect(self.change_language)
        lang_layout.addWidget(self.lang_combo)
        
        main_layout.addLayout(lang_layout)
                
        # Title label
        self.title_label = QLabel(TRANSLATIONS["main"][self.current_lang]["title"])
        self.title_label.setAlignment(Qt.AlignCenter)
        self.title_label.setStyleSheet("font-size: 20px; font-weight: bold; margin-bottom: 5px;")
        main_layout.addWidget(self.title_label)
        
        # Description label
        self.description_label = QLabel(TRANSLATIONS["main"][self.current_lang]["description"])
        self.description_label.setAlignment(Qt.AlignCenter)
        self.description_label.setStyleSheet("font-size: 12px; margin-bottom: 10px;")
        main_layout.addWidget(self.description_label)
        
        # Button group
        button_layout = QVBoxLayout()
        button_layout.setSpacing(10)
        
        # Enrichment App Button
        self.enrichment_app_btn = QPushButton(TRANSLATIONS["main"][self.current_lang]["enrichment_btn"])
        self.enrichment_app_btn.setMinimumHeight(50)
        self.enrichment_app_btn.clicked.connect(self.open_enrichment_app)
        button_layout.addWidget(self.enrichment_app_btn)
        
        # GSEA Visualization Button
        self.gsea_vis_btn = QPushButton(TRANSLATIONS["main"][self.current_lang]["vis_btn"])
        self.gsea_vis_btn.setMinimumHeight(50)
        self.gsea_vis_btn.clicked.connect(self.open_gsea_vis)
        button_layout.addWidget(self.gsea_vis_btn)
        
        # GMT Generator Button
        self.gmt_gen_btn = QPushButton(TRANSLATIONS["main"][self.current_lang]["gmt_btn"])
        self.gmt_gen_btn.setMinimumHeight(50)
        self.gmt_gen_btn.clicked.connect(self.open_gmt_gen)
        button_layout.addWidget(self.gmt_gen_btn)
        
        main_layout.addLayout(button_layout)
        
        # Add stretch to push bottom info to the bottom
        main_layout.addStretch()
        
        # Bottom info layout (Version and GitHub link)
        bottom_layout = QHBoxLayout()
        
        # GitHub Homepage Link
        self.github_label = QLabel(f'<a href="https://github.com/byemaxx/gseaGUI">{TRANSLATIONS["main"][self.current_lang]["github_btn"]}</a>')
        self.github_label.setOpenExternalLinks(True)
        self.github_label.setAlignment(Qt.AlignLeft)
        bottom_layout.addWidget(self.github_label)
        
        bottom_layout.addStretch()
        
        # Version label
        self.version_label = QLabel(
            TRANSLATIONS["main"][self.current_lang]["version"].format(version=APP_VERSION)
        )
        self.version_label.setAlignment(Qt.AlignRight)
        bottom_layout.addWidget(self.version_label)
        
        main_layout.addLayout(bottom_layout)
        
        # Save window references
        self.enrichment_app_window = None
        self.gsea_vis_window = None
        self.gmt_gen_window = None
    
    def center(self):
        """Center the window on screen"""
        from PyQt5.QtWidgets import QDesktopWidget
        qr = self.frameGeometry()
        cp = QDesktopWidget().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())

    def change_language(self, index):
        """Change the application language"""
        lang_code = self.lang_combo.itemData(index)
        if lang_code != self.current_lang:
            self.current_lang = lang_code
            self.update_ui_text()
    
    def update_ui_text(self):
        """Update UI text based on current language"""
        texts = TRANSLATIONS["main"][self.current_lang]
        
        self.setWindowTitle(texts["window_title"])
        self.title_label.setText(texts["title"])
        self.description_label.setText(texts["description"])
        self.enrichment_app_btn.setText(texts["enrichment_btn"])
        self.gsea_vis_btn.setText(texts["vis_btn"])
        self.gmt_gen_btn.setText(texts["gmt_btn"])
        self.github_label.setText(f'<a href="https://github.com/byemaxx/gseaGUI">{texts["github_btn"]}</a>')
        self.version_label.setText(texts["version"].format(version=APP_VERSION))
    
    def open_enrichment_app(self):
        """Open Enrichment App Window"""
        self.enrichment_app_window = EnrichmentApp(lang=self.current_lang)
        self.enrichment_app_window.show()
    
    def open_gsea_vis(self):
        """Open GSEA Visualization Window"""
        self.gsea_vis_window = GSEAVisualizationGUI(lang=self.current_lang)
        self.gsea_vis_window.show()
    
    def open_gmt_gen(self):
        """Open GMT Generator Window"""
        self.gmt_gen_window = GMTGenerator(lang=self.current_lang)
        self.gmt_gen_window.show()

def main():
    # Configure HiDPI behavior before QApplication is created.
    set_qt_highdpi_attributes()
    app = QApplication(sys.argv)

    # Slightly shrink UI on HiDPI by default; override via env var `GSEAGUI_UI_SCALE`.
    apply_application_ui_scale(app)

    window = MainGUI()
    window.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
