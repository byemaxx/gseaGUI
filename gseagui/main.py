import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QPushButton, QLabel, QComboBox, QHBoxLayout
from PyQt5.QtCore import Qt

try:
    from gseagui.gsea_res_ploter import GSEAVisualizationGUI
    from gseagui.gmt_generator import GMTGenerator
    from gseagui.gsea_runner import EnrichmentApp
    from gseagui.translations import TRANSLATIONS
except ImportError:
    from gsea_res_ploter import GSEAVisualizationGUI
    from gmt_generator import GMTGenerator
    from gsea_runner import EnrichmentApp
    from translations import TRANSLATIONS

class MainGUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.current_lang = "en"  # Default to English
        
        self.setWindowTitle(TRANSLATIONS["main"][self.current_lang]["window_title"])
        self.setGeometry(100, 100, 800, 600)
        
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
        self.title_label.setStyleSheet("font-size: 20px; font-weight: bold;")
        main_layout.addWidget(self.title_label)
        
        # Description label
        self.description_label = QLabel(TRANSLATIONS["main"][self.current_lang]["description"])
        self.description_label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(self.description_label)
        
        # Button group
        button_layout = QVBoxLayout()
        
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
        
        # Version label
        self.version_label = QLabel(TRANSLATIONS["main"][self.current_lang]["version"])
        self.version_label.setAlignment(Qt.AlignRight)
        main_layout.addWidget(self.version_label)
        
        # Save window references
        self.enrichment_app_window = None
        self.gsea_vis_window = None
        self.gmt_gen_window = None

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
        self.version_label.setText(texts["version"])
    
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
    app = QApplication(sys.argv)
    window = MainGUI()
    window.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
