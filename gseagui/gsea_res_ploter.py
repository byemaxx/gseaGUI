import sys
import pandas as pd
import pickle
import warnings
import matplotlib
try:
    matplotlib.use('QtAgg')
except Exception:
    matplotlib.use('Qt5Agg')
from gseapy import barplot, dotplot
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt import NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure, SubFigure
from matplotlib.axes import Axes
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                             QPushButton, QLabel, QComboBox, QFileDialog, QTabWidget, 
                             QSpinBox, QDoubleSpinBox, QCheckBox, QGroupBox, QListWidget,
                             QGridLayout, QLineEdit, QColorDialog, QMessageBox, QMenu, QDialog, QDialogButtonBox,
                             QListWidgetItem, QScrollArea, QToolButton, QSizePolicy)
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QAbstractItemView

try:
    from gseagui.qt_utils import fit_window_to_available_screen
except ImportError:
    from qt_utils import fit_window_to_available_screen

try:
    from gseagui.translations import TRANSLATIONS
except ImportError:
    from translations import TRANSLATIONS

class GSEAVisualizationGUI(QMainWindow):
    def __init__(self, lang='en'):
        super().__init__()
        self.lang = lang
        self.trans = TRANSLATIONS["ploter"][self.lang]
        
        self.setWindowTitle(self.trans["window_title"])
        fit_window_to_available_screen(self, 850, 600, max_ratio=0.65)
        
        # 数据存储
        self.tsv_data = None
        self.gsea_result = None
        self.current_file_type = None
        self.column_names = []
        self.colors = {}
        self.mpl_style = "default"

        # TSV: 通用列过滤（任意列 -> 多选取值）
        self._data_filter_column: str | None = None
        self._data_filter_selected_values: set[str] = set()
        self._data_filter_available_values: list[str] = []
        
        # 初始化UI
        self.init_ui()

        # 应用默认主题（不弹窗）
        self.set_mpl_style(self.mpl_style, silent=True)
        
    def init_ui(self):
        """初始化主UI"""
        # 创建中央窗口部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 主布局
        main_layout = QVBoxLayout(central_widget)
        
        # 控制面板
        control_panel = QWidget()
        control_layout = QVBoxLayout(control_panel)
        
        # 文件加载部分
        file_group = QGroupBox(self.trans["file_load_group"])
        file_layout = QVBoxLayout(file_group)
        
        self.load_file_btn = QPushButton(self.trans["load_file_btn"])
        self.load_file_btn.clicked.connect(self.load_file)
        file_layout.addWidget(self.load_file_btn)
        
        self.file_path_label = QLabel(self.trans["no_file"])
        file_layout.addWidget(self.file_path_label)
        
        control_layout.addWidget(file_group)
        
        # 创建选项卡部件
        self.tab_widget = QTabWidget()
        
        # TSV选项卡
        self.tsv_tab = QWidget()
        tsv_layout = QVBoxLayout(self.tsv_tab)

        # TSV 内部滚动容器（避免控件多导致窗口被撑高）
        tsv_scroll = QScrollArea()
        tsv_scroll.setWidgetResizable(True)
        tsv_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        tsv_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        tsv_scroll.setFrameShape(QScrollArea.NoFrame)

        tsv_inner = QWidget()
        tsv_inner_layout = QVBoxLayout(tsv_inner)
        tsv_inner_layout.setContentsMargins(0, 0, 0, 0)
        tsv_inner_layout.setSpacing(8)
        tsv_scroll.setWidget(tsv_inner)

        tsv_layout.addWidget(tsv_scroll)

        def _make_collapsible(title: str, content: QWidget, *, collapsed: bool = False) -> QWidget:
            container = QWidget()
            container_layout = QVBoxLayout(container)
            container_layout.setContentsMargins(0, 0, 0, 0)
            container_layout.setSpacing(2)

            toggle = QToolButton()
            toggle.setText(title)
            toggle.setCheckable(True)
            toggle.setChecked(not collapsed)
            toggle.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
            toggle.setArrowType(Qt.DownArrow if not collapsed else Qt.RightArrow)
            toggle.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

            content.setVisible(not collapsed)

            def _on_toggled(checked: bool):
                content.setVisible(checked)
                toggle.setArrowType(Qt.DownArrow if checked else Qt.RightArrow)
                # 触发布局重新计算
                container.adjustSize()

            toggle.toggled.connect(_on_toggled)

            container_layout.addWidget(toggle)
            container_layout.addWidget(content)
            return container

        # =====================
        # 数据过滤（放到 TSV 页最上面）
        # =====================
        data_filter_group = QGroupBox(self.trans.get("data_filter_group", "Data Filter"))
        data_filter_layout = QGridLayout(data_filter_group)

        data_filter_layout.addWidget(QLabel(self.trans.get("data_filter_column", "Filter column:")), 0, 0)
        self.data_filter_column_combo = QComboBox()
        self.data_filter_column_combo.addItem("")
        self.data_filter_column_combo.currentIndexChanged.connect(self.on_data_filter_column_changed)
        data_filter_layout.addWidget(self.data_filter_column_combo, 0, 1)

        self.data_filter_btn = QPushButton(self.trans.get("data_filter_btn", "Filter values..."))
        self.data_filter_btn.clicked.connect(self.open_data_filter_dialog)
        self.data_filter_btn.setEnabled(False)
        data_filter_layout.addWidget(self.data_filter_btn, 0, 2)

        self.data_filter_status_label = QLabel("")
        self.data_filter_status_label.setStyleSheet("color: #666666; font-size: 11px;")
        self.data_filter_status_label.setWordWrap(True)
        data_filter_layout.addWidget(self.data_filter_status_label, 1, 0, 1, 3)

        tsv_inner_layout.addWidget(data_filter_group)
        
        # 绘图类型
        plot_type_group = QGroupBox(self.trans["plot_type_group"])
        plot_type_layout = QVBoxLayout(plot_type_group)
        
        self.plot_type_combo = QComboBox()
        self.plot_type_combo.addItems(["Dot Plot", "Bar Plot"])
        self.plot_type_combo.currentIndexChanged.connect(self.update_plot_options)
        self.plot_type_combo.currentIndexChanged.connect(self.update_axis_hints)
        plot_type_layout.addWidget(self.plot_type_combo)

        # 轴含义提示：明确X/Y分别是什么
        self.axis_hint_label = QLabel("")
        self.axis_hint_label.setWordWrap(True)
        self.axis_hint_label.setStyleSheet("color: #444444; font-size: 11px;")
        plot_type_layout.addWidget(self.axis_hint_label)
        
        tsv_inner_layout.addWidget(plot_type_group)
        
        # 基本参数
        self.basic_param_group = QGroupBox(self.trans["basic_param_group"])
        basic_param_layout = QGridLayout(self.basic_param_group)

        # 左侧标签列太窄时会被裁剪：设置最小宽度并允许换行
        basic_param_layout.setColumnMinimumWidth(0, 180)

        _lbl = QLabel(self.trans.get("term_column", "Y-axis (Term) Column:"))
        _lbl.setWordWrap(True)
        basic_param_layout.addWidget(_lbl, 0, 0)
        self.term_column_combo = QComboBox()
        self.term_column_combo.currentIndexChanged.connect(self.update_preview)
        self.term_column_combo.currentIndexChanged.connect(self.update_axis_hints)
        basic_param_layout.addWidget(self.term_column_combo, 0, 1)
        
        _lbl = QLabel(self.trans["column"])
        _lbl.setWordWrap(True)
        basic_param_layout.addWidget(_lbl, 1, 0)
        self.column_combo = QComboBox()
        self.column_combo.currentIndexChanged.connect(self.update_preview)
        basic_param_layout.addWidget(self.column_combo, 1, 1)
        
        _lbl = QLabel(self.trans["x_group"])
        _lbl.setWordWrap(True)
        basic_param_layout.addWidget(_lbl, 2, 0)
        self.x_combo = QComboBox()
        self.x_combo.currentIndexChanged.connect(self.update_preview)
        self.x_combo.currentIndexChanged.connect(self.update_axis_hints)

        basic_param_layout.addWidget(self.x_combo, 2, 1)
        
        _lbl = QLabel(self.trans["hue"])
        _lbl.setWordWrap(True)
        basic_param_layout.addWidget(_lbl, 3, 0)
        self.hue_combo = QComboBox()
        self.hue_combo.currentIndexChanged.connect(self.update_preview)
        basic_param_layout.addWidget(self.hue_combo, 3, 1)
        
        _lbl = QLabel(self.trans["threshold"])
        _lbl.setWordWrap(True)
        basic_param_layout.addWidget(_lbl, 4, 0)
        self.thresh_spin = QDoubleSpinBox()
        self.thresh_spin.setRange(0, 1)
        self.thresh_spin.setDecimals(3)
        self.thresh_spin.setSingleStep(0.001)
        self.thresh_spin.setValue(0.05)
        self.thresh_spin.valueChanged.connect(self.update_preview)
        self.thresh_spin.valueChanged.connect(self.update_axis_hints)
        basic_param_layout.addWidget(self.thresh_spin, 4, 1)
        
        _lbl = QLabel(self.trans["top_term"])
        _lbl.setWordWrap(True)
        basic_param_layout.addWidget(_lbl, 5, 0)
        self.top_term_spin = QSpinBox()
        self.top_term_spin.setRange(1, 500)
        self.top_term_spin.setValue(10)
        self.top_term_spin.valueChanged.connect(self.update_preview)
        self.top_term_spin.valueChanged.connect(self.update_axis_hints)
        basic_param_layout.addWidget(self.top_term_spin, 5, 1)

        self.top_term_per_group_check = QCheckBox(self.trans.get("top_term_per_group", "Top N per group"))
        self.top_term_per_group_check.setChecked(True)
        self.top_term_per_group_check.stateChanged.connect(self.update_preview)
        self.top_term_per_group_check.stateChanged.connect(self.update_axis_hints)
        basic_param_layout.addWidget(self.top_term_per_group_check, 6, 0, 1, 2)

        # Hypergeometric/ORA 常见过滤与排序
        filter_group = QGroupBox(self.trans.get("filter_sort_group", "Filter & Sort"))
        filter_layout = QGridLayout(filter_group)

        filter_layout.addWidget(QLabel(self.trans.get("sort_by", "Sort by:")), 0, 0)
        self.sort_by_combo = QComboBox()
        self.sort_by_combo.currentIndexChanged.connect(self.update_preview)
        self.sort_by_combo.currentIndexChanged.connect(self.update_axis_hints)
        filter_layout.addWidget(self.sort_by_combo, 0, 1)

        filter_layout.addWidget(QLabel(self.trans.get("sort_order", "Order:")), 1, 0)
        self.sort_order_combo = QComboBox()
        self.sort_order_combo.addItems([
            self.trans.get("sort_order_asc", "Ascending"),
            self.trans.get("sort_order_desc", "Descending"),
        ])
        self.sort_order_combo.currentIndexChanged.connect(self.update_preview)
        self.sort_order_combo.currentIndexChanged.connect(self.update_axis_hints)
        filter_layout.addWidget(self.sort_order_combo, 1, 1)

        filter_layout.addWidget(QLabel(self.trans.get("min_overlap", "Min overlap:")), 2, 0)
        self.min_overlap_spin = QSpinBox()
        self.min_overlap_spin.setRange(0, 10_000_000)
        self.min_overlap_spin.setValue(0)
        self.min_overlap_spin.valueChanged.connect(self.update_preview)
        self.min_overlap_spin.valueChanged.connect(self.update_axis_hints)
        filter_layout.addWidget(self.min_overlap_spin, 2, 1)

        filter_layout.addWidget(QLabel(self.trans.get("min_gene_ratio", "Min gene ratio:")), 3, 0)
        self.min_gene_ratio_spin = QDoubleSpinBox()
        self.min_gene_ratio_spin.setRange(0, 1)
        self.min_gene_ratio_spin.setDecimals(3)
        self.min_gene_ratio_spin.setSingleStep(0.01)
        self.min_gene_ratio_spin.setValue(0.0)
        self.min_gene_ratio_spin.valueChanged.connect(self.update_preview)
        self.min_gene_ratio_spin.valueChanged.connect(self.update_axis_hints)
        filter_layout.addWidget(self.min_gene_ratio_spin, 3, 1)

        # 过滤/排序也比较占空间，放到可折叠区（默认展开）
        filter_title = filter_group.title()
        filter_group.setTitle("")
        self.filter_section = _make_collapsible(filter_title, filter_group, collapsed=False)
        tsv_inner_layout.addWidget(self.filter_section)
        
        _lbl = QLabel(self.trans["img_size"])
        _lbl.setWordWrap(True)
        basic_param_layout.addWidget(_lbl, 7, 0)
        size_layout = QHBoxLayout()
        self.width_spin = QSpinBox()
        self.width_spin.setRange(1, 20)
        self.width_spin.setValue(10)
        self.height_spin = QSpinBox()
        self.height_spin.setRange(1, 20)
        self.height_spin.setValue(5)
        size_layout.addWidget(self.width_spin)
        size_layout.addWidget(QLabel("x"))
        size_layout.addWidget(self.height_spin)
        basic_param_layout.addLayout(size_layout, 7, 1)
        
        _lbl = QLabel(self.trans["title"])
        _lbl.setWordWrap(True)
        basic_param_layout.addWidget(_lbl, 8, 0)
        self.title_edit = QLineEdit("")
        basic_param_layout.addWidget(self.title_edit, 8, 1)
        
        # 在基本参数组中添加轴标签字体大小设置
        _lbl = QLabel(self.trans["x_axis_fontsize"])
        _lbl.setWordWrap(True)
        basic_param_layout.addWidget(_lbl, 9, 0)
        self.x_axis_fontsize_spin = QSpinBox()
        self.x_axis_fontsize_spin.setRange(5, 24)
        self.x_axis_fontsize_spin.setValue(14)
        basic_param_layout.addWidget(self.x_axis_fontsize_spin, 9, 1)
        
        _lbl = QLabel(self.trans["y_axis_fontsize"])
        _lbl.setWordWrap(True)
        basic_param_layout.addWidget(_lbl, 10, 0)
        self.y_axis_fontsize_spin = QSpinBox()
        self.y_axis_fontsize_spin.setRange(5, 24)
        self.y_axis_fontsize_spin.setValue(14)
        basic_param_layout.addWidget(self.y_axis_fontsize_spin, 10, 1)

        # Matplotlib主题/样式
        _lbl = QLabel(self.trans["mpl_style"])
        _lbl.setWordWrap(True)
        basic_param_layout.addWidget(_lbl, 11, 0)
        self.mpl_style_combo = QComboBox()
        self.mpl_style_combo.addItems(self.get_available_mpl_styles())
        self.mpl_style_combo.setCurrentText(self.mpl_style)
        self.mpl_style_combo.currentIndexChanged.connect(self.on_mpl_style_changed)
        basic_param_layout.addWidget(self.mpl_style_combo, 11, 1)
        
        # Basic Parameters 放入可折叠区（默认展开）
        basic_title = self.basic_param_group.title()
        self.basic_param_group.setTitle("")
        self.basic_param_section = _make_collapsible(basic_title, self.basic_param_group, collapsed=False)
        tsv_inner_layout.addWidget(self.basic_param_section)

        # X/Group 值筛选改为按钮弹窗，不在主界面占空间
        
        # Dot Plot特定参数
        self.dot_param_group = QGroupBox(self.trans["dot_param_group"])
        dot_param_layout = QGridLayout(self.dot_param_group)
        
        dot_param_layout.addWidget(QLabel(self.trans["dot_scale"]), 0, 0)
        self.dot_scale_spin = QDoubleSpinBox()
        self.dot_scale_spin.setRange(1, 20)
        self.dot_scale_spin.setValue(3)
        self.dot_scale_spin.valueChanged.connect(self.update_preview)
        dot_param_layout.addWidget(self.dot_scale_spin, 0, 1)
        
        dot_param_layout.addWidget(QLabel(self.trans["marker_shape"]), 1, 0)
        self.marker_combo = QComboBox()
        self.marker_combo.addItems(["o", "s", "^", "D", "*", "p", "h", "8"])
        self.marker_combo.currentIndexChanged.connect(self.update_preview)
        dot_param_layout.addWidget(self.marker_combo, 1, 1)
        
        dot_param_layout.addWidget(QLabel(self.trans["colormap"]), 2, 0)
        self.cmap_combo = QComboBox()
        self.cmap_combo.addItems(["viridis", "viridis_r", "plasma", "plasma_r", "Blues", "Blues_r", "Reds", "Reds_r"])
        self.cmap_combo.currentIndexChanged.connect(self.update_preview)
        dot_param_layout.addWidget(self.cmap_combo, 2, 1)
        
        self.show_ring_check = QCheckBox(self.trans["show_ring"])
        self.show_ring_check.setChecked(True)
        self.show_ring_check.stateChanged.connect(self.update_preview)
        dot_param_layout.addWidget(self.show_ring_check, 3, 0, 1, 2)
        
        dot_param_layout.addWidget(QLabel(self.trans["label_rot"]), 4, 0)
        self.xticklabels_rot_spin = QSpinBox()
        self.xticklabels_rot_spin.setRange(0, 90)
        self.xticklabels_rot_spin.setValue(45)
        self.xticklabels_rot_spin.valueChanged.connect(self.update_preview)
        dot_param_layout.addWidget(self.xticklabels_rot_spin, 4, 1)
        
        # 修改Dot Plot参数组中的legend设置 - 只保留字体大小设置
        dot_param_layout.addWidget(QLabel(self.trans["legend_fontsize"]), 5, 0)
        self.legend_fontsize_spin = QSpinBox()
        self.legend_fontsize_spin.setRange(5, 18)
        self.legend_fontsize_spin.setValue(10)
        dot_param_layout.addWidget(self.legend_fontsize_spin, 5, 1)
        
        # 移除图例位置和外部显示的控制选项
        
        dot_title = self.dot_param_group.title()
        self.dot_param_group.setTitle("")
        self.dot_param_section = _make_collapsible(dot_title, self.dot_param_group, collapsed=False)
        tsv_inner_layout.addWidget(self.dot_param_section)
        
        # Bar Plot特定参数
        self.bar_param_group = QGroupBox(self.trans["bar_param_group"])
        bar_param_layout = QVBoxLayout(self.bar_param_group)
        
        # 颜色选择
        self.color_list = QListWidget()
        self.color_list.setMaximumHeight(150)
        bar_param_layout.addWidget(self.color_list)
        
        color_btn_layout = QHBoxLayout()
        self.add_color_btn = QPushButton(self.trans["add_color"])
        self.add_color_btn.clicked.connect(self.add_color)
        self.remove_color_btn = QPushButton(self.trans["remove_color"])
        self.remove_color_btn.clicked.connect(self.remove_color)
        color_btn_layout.addWidget(self.add_color_btn)
        color_btn_layout.addWidget(self.remove_color_btn)
        
        bar_param_layout.addLayout(color_btn_layout)
        
        # 在Bar Plot参数组中也只保留字体大小设置
        bar_param_layout.addWidget(QLabel(self.trans["legend_fontsize"]))
        self.bar_legend_fontsize_spin = QSpinBox()
        self.bar_legend_fontsize_spin.setRange(6, 18)
        self.bar_legend_fontsize_spin.setValue(8)
        bar_param_layout.addWidget(self.bar_legend_fontsize_spin)
        
        # 在 Bar Plot 参数组中添加 legend 位置设置
        bar_param_layout.addWidget(QLabel(self.trans["legend_pos"]))
        self.bar_legend_pos_combo = QComboBox()
        self.bar_legend_pos_combo.addItems(["right", "center left", "center right", "lower center", "upper center", "best"])
        self.bar_legend_pos_combo.setCurrentText("center right")
        bar_param_layout.addWidget(self.bar_legend_pos_combo)
        
        bar_title = self.bar_param_group.title()
        self.bar_param_group.setTitle("")
        self.bar_param_section = _make_collapsible(bar_title, self.bar_param_group, collapsed=False)
        tsv_inner_layout.addWidget(self.bar_param_section)
        self.bar_param_section.hide()  # 初始隐藏
        
        # 顶部对齐，底部留伸缩空间
        tsv_inner_layout.addStretch(1)

        # 绘图按钮：放在滚动窗口之外，始终可见
        self.plot_button = QPushButton(self.trans["plot_btn"])
        self.plot_button.clicked.connect(self.plot_chart)
        tsv_layout.addWidget(self.plot_button)
        
        # PKL选项卡
        self.pkl_tab = QWidget()
        pkl_layout = QVBoxLayout(self.pkl_tab)
        
        # Term选择
        term_group = QGroupBox(self.trans["term_select_group"])
        term_layout = QVBoxLayout(term_group)
        
        self.term_list = QListWidget()
        self.term_list.setSelectionMode(QListWidget.MultiSelection)
        self.term_list.setContextMenuPolicy(Qt.CustomContextMenu)  # 设置自定义上下文菜单
        self.term_list.customContextMenuRequested.connect(self.show_term_context_menu)  # 连接右键菜单信号
        term_layout.addWidget(self.term_list)
        
        self.show_ranking_check = QCheckBox(self.trans["show_ranking"])
        self.show_ranking_check.setChecked(False)
        term_layout.addWidget(self.show_ranking_check)
        
        # GSEA绘图尺寸和字体设置
        gsea_param_group = QGroupBox(self.trans["gsea_param_group"])
        gsea_param_layout = QGridLayout(gsea_param_group)
        
        gsea_param_layout.addWidget(QLabel(self.trans["img_size"]), 0, 0)
        gsea_size_layout = QHBoxLayout()
        self.gsea_width_spin = QSpinBox()
        self.gsea_width_spin.setRange(4, 20)
        self.gsea_width_spin.setValue(10)
        self.gsea_height_spin = QSpinBox()
        self.gsea_height_spin.setRange(3, 20)
        self.gsea_height_spin.setValue(8)
        gsea_size_layout.addWidget(self.gsea_width_spin)
        gsea_size_layout.addWidget(QLabel("x"))
        gsea_size_layout.addWidget(self.gsea_height_spin)
        gsea_param_layout.addLayout(gsea_size_layout, 0, 1)
        
        gsea_param_layout.addWidget(QLabel(self.trans["label_fontsize"]), 1, 0)
        self.gsea_fontsize_spin = QSpinBox()
        self.gsea_fontsize_spin.setRange(5, 20)
        self.gsea_fontsize_spin.setValue(12)
        gsea_param_layout.addWidget(self.gsea_fontsize_spin, 1, 1)
        
        # 在GSEA绘图参数中保留完整的图例设置
        gsea_param_layout.addWidget(QLabel(self.trans["legend_pos"]), 2, 0)
        self.gsea_legend_pos_combo = QComboBox()
        self.gsea_legend_pos_combo.addItems(["right", "center left", "center right", "lower center", "upper center", "best"])
        self.gsea_legend_pos_combo.setCurrentText("best")  # 默认为best
        gsea_param_layout.addWidget(self.gsea_legend_pos_combo, 2, 1)
        
        gsea_param_layout.addWidget(QLabel(self.trans["legend_fontsize"]), 3, 0)
        self.gsea_legend_fontsize_spin = QSpinBox()
        self.gsea_legend_fontsize_spin.setRange(5, 18)
        self.gsea_legend_fontsize_spin.setValue(6)  # 默认字体大小为6
        gsea_param_layout.addWidget(self.gsea_legend_fontsize_spin, 3, 1)
        
        # 添加图例位置控制选项
        gsea_param_layout.addWidget(QLabel(self.trans["legend_outside"]), 4, 0)
        self.gsea_legend_outside_check = QCheckBox()
        self.gsea_legend_outside_check.setChecked(False)  # 默认在图内
        gsea_param_layout.addWidget(self.gsea_legend_outside_check, 4, 1)
        
        term_layout.addWidget(gsea_param_group)
        
        pkl_layout.addWidget(term_group)
        
        # 绘图按钮
        self.gsea_plot_button = QPushButton(self.trans["plot_gsea_btn"])
        self.gsea_plot_button.clicked.connect(self.plot_gsea)
        pkl_layout.addWidget(self.gsea_plot_button)
        
        # 将选项卡添加到选项卡部件
        self.tab_widget.addTab(self.tsv_tab, self.trans["tab_tsv"])
        self.tab_widget.addTab(self.pkl_tab, self.trans["tab_gsea"])
        self.tab_widget.setTabEnabled(0, False)
        self.tab_widget.setTabEnabled(1, False)
        
        control_layout.addWidget(self.tab_widget)
        
        # 添加控制面板到主布局
        main_layout.addWidget(control_panel)

    def _show_figure_in_window(self, fig, window_title: str):
        """在独立Qt窗口中嵌入显示 Matplotlib Figure，避免不同后端/事件循环导致空白窗口。"""
        plot_window = QMainWindow()
        plot_window.setWindowTitle(window_title)
        plot_window.resize(1200, 800)

        central_widget = QWidget()
        plot_window.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)

        canvas = FigureCanvas(fig)
        toolbar = NavigationToolbar(canvas, plot_window)
        layout.addWidget(toolbar)
        layout.addWidget(canvas)

        fig.tight_layout()
        canvas.draw()
        plot_window.show()

        # 保持窗口引用，避免被GC回收导致窗口/画布异常
        if not hasattr(self, "_plot_windows"):
            self._plot_windows = []
        self._plot_windows.append(plot_window)
        return plot_window
        
    def load_file(self):
        """加载文件（TSV或PKL）"""
        options = QFileDialog.Options()
        # 修改对话框内容，默认即可选TSV或PKL
        file_filter = "数据文件 (*.tsv *.pkl);;TSV文件 (*.tsv);;PKL文件 (*.pkl);;所有文件 (*)"
        file_path, _ = QFileDialog.getOpenFileName(
            self, "选择文件", "", file_filter, options=options)
        
        if not file_path:
            return
            
        self.file_path_label.setText(file_path)
        
        # 根据文件类型处理
        if file_path.lower().endswith('.tsv'):
            self.load_tsv_file(file_path)
        elif file_path.lower().endswith('.pkl'):
            self.load_pkl_file(file_path)
        else:
            QMessageBox.warning(self, self.trans["msg_unsupported_type"], self.trans["msg_select_tsv_pkl"])
    
    def load_tsv_file(self, file_path):
        """加载TSV文件"""
        try:
            self.tsv_data = pd.read_csv(file_path, sep='\t')
            self.current_file_type = 'tsv'
            
            # 更新列选择框
            self.column_names = list(self.tsv_data.columns)
            self.column_combo.clear()
            self.x_combo.clear()
            self.hue_combo.clear()
            self.term_column_combo.clear()
            self.sort_by_combo.clear()
            
            self.column_combo.addItems(self.column_names)
            self.x_combo.addItems(self.column_names)
            self.hue_combo.addItem("")
            self.hue_combo.addItems(self.column_names)
            self.term_column_combo.addItems(self.column_names)
            self.sort_by_combo.addItems(self._get_sort_candidates(self.column_names))

            # 通用过滤列下拉
            if hasattr(self, "data_filter_column_combo"):
                self.data_filter_column_combo.blockSignals(True)
                self.data_filter_column_combo.clear()
                self.data_filter_column_combo.addItem("")
                self.data_filter_column_combo.addItems(self.column_names)
                self.data_filter_column_combo.setCurrentIndex(0)
                self.data_filter_column_combo.blockSignals(False)

                # 重置过滤状态
                self._data_filter_column = None
                self._data_filter_selected_values = set()
                self._data_filter_available_values = []
                self.data_filter_btn.setEnabled(False)
                self.update_data_filter_status_label()
            
            # 预设常见值（如果存在）
            self.set_default_columns()
            
            # 启用TSV选项卡
            self.tab_widget.setTabEnabled(0, True)
            self.tab_widget.setTabEnabled(1, False)
            self.tab_widget.setCurrentIndex(0)
            
            QMessageBox.information(self, self.trans["msg_load_success"], self.trans["msg_tsv_loaded"].format(len(self.tsv_data)))
            
        except Exception as e:
            QMessageBox.critical(self, self.trans["msg_load_fail"], f"{self.trans['msg_load_fail']}: {str(e)}")

    # =====================
    # 通用列过滤（任意列）
    # =====================
    def on_data_filter_column_changed(self, _=None):
        self.refresh_data_filter(reset_selection=True)
        self.update_preview()

    def refresh_data_filter(self, reset_selection: bool = False):
        if self.tsv_data is None:
            return
        if not hasattr(self, "data_filter_column_combo"):
            return

        column_name = self.data_filter_column_combo.currentText().strip()
        if not column_name:
            self._data_filter_column = None
            self._data_filter_selected_values = set()
            self._data_filter_available_values = []
            if hasattr(self, "data_filter_btn"):
                self.data_filter_btn.setEnabled(False)
            self.update_data_filter_status_label()
            return

        if column_name not in self.tsv_data.columns:
            self._data_filter_column = None
            self._data_filter_selected_values = set()
            self._data_filter_available_values = []
            self.data_filter_btn.setEnabled(False)
            self.update_data_filter_status_label()
            return

        values = (
            self.tsv_data[column_name]
            .dropna()
            .astype(str)
            .unique()
            .tolist()
        )
        values = sorted(values)
        self._data_filter_available_values = values

        column_changed = (self._data_filter_column != column_name)
        if column_changed:
            self._data_filter_column = column_name
            self._data_filter_selected_values = set()
            reset_selection = True

        if reset_selection or not self._data_filter_selected_values:
            self._data_filter_selected_values = set(values)
        else:
            self._data_filter_selected_values = self._data_filter_selected_values.intersection(values)

        self.data_filter_btn.setEnabled(True)
        self.update_data_filter_status_label()

    def update_data_filter_status_label(self):
        if not hasattr(self, "data_filter_status_label"):
            return
        if not self._data_filter_column:
            self.data_filter_status_label.setText(self.trans.get("data_filter_status_none", "No filter applied"))
            return

        total = len(self._data_filter_available_values)
        selected = len(self._data_filter_selected_values)
        if total == 0:
            self.data_filter_status_label.setText(self.trans.get("data_filter_status_empty", "No values"))
        elif selected == total:
            self.data_filter_status_label.setText(
                self.trans.get("data_filter_status_all", "Selected all ({} values)").format(total)
            )
        else:
            self.data_filter_status_label.setText(
                self.trans.get("data_filter_status_some", "Selected {}/{} values").format(selected, total)
            )

    def open_data_filter_dialog(self):
        if self.tsv_data is None:
            QMessageBox.warning(self, self.trans["msg_error"], self.trans["msg_load_tsv_first"])
            return

        self.refresh_data_filter(reset_selection=False)
        if not self._data_filter_column:
            return

        dlg = XValueFilterDialog(
            parent=self,
            title=self.trans.get("data_filter_dialog_title", "Filter values for: {}").format(self._data_filter_column),
            values=self._data_filter_available_values,
            selected_values=self._data_filter_selected_values,
            trans=self.trans,
            empty_selection_message=self.trans.get(
                "msg_no_filter_values_selected",
                "No values selected. Please select at least one.",
            ),
        )
        if dlg.exec_() == QDialog.Accepted:
            self._data_filter_selected_values = set(dlg.get_selected_values())
            self.update_data_filter_status_label()
            self.update_preview()

    def get_selected_data_filter_values(self) -> list[str]:
        if self.tsv_data is None:
            return []
        if not self._data_filter_column:
            return []
        if not self._data_filter_selected_values:
            return []
        return sorted(self._data_filter_selected_values)
    
    def load_pkl_file(self, file_path):
        """加载PKL文件"""
        try:
            with open(file_path, 'rb') as f:
                self.gsea_result = pickle.load(f)
            
            self.current_file_type = 'pkl'
            
            # 填充Term列表
            self.term_list.clear()
            terms = self.gsea_result.res2d.Term
            for term in terms:
                self.term_list.addItem(term)
            
            # 启用PKL选项卡
            self.tab_widget.setTabEnabled(0, False)
            self.tab_widget.setTabEnabled(1, True)
            self.tab_widget.setCurrentIndex(1)
            
            QMessageBox.information(self, self.trans["msg_load_success"], self.trans["msg_pkl_loaded"].format(len(terms)))
            
        except Exception as e:
            QMessageBox.critical(self, self.trans["msg_load_fail"], f"{self.trans['msg_load_fail']}: {str(e)}")
    
    def set_default_columns(self):
        """设置默认列名（如果存在）"""
        column_indices = {}
        
        # 查找常见的列名
        possible_column_names = ["Adjusted P-value", "P-value", "pvalue", "p-value", "p_value", "padj"]
        for i, name in enumerate(self.column_names):
            for possible_name in possible_column_names:
                if possible_name.lower() in name.lower():
                    column_indices["column"] = i
                    break
        
        # 优先选择 Gene_set 和 Name 作为 x_combo 的默认值
        for priority_name in ["Gene_set", "Name", "Term", "Pathway", "ID"]:
            for i, name in enumerate(self.column_names):
                if priority_name.lower() in name.lower():
                    column_indices["x"] = i
                    break
            if "x" in column_indices:
                break  # 如果找到了，就不再继续查找
        
        # 设置默认值
        if "column" in column_indices:
            self.column_combo.setCurrentIndex(column_indices["column"])
        if "x" in column_indices:
            self.x_combo.setCurrentIndex(column_indices["x"])
            
        # 对于hue，默认使用与column相同的值
        try:
            # hue_combo 第一个是空值，后面才是列名
            if "column" in column_indices:
                self.hue_combo.setCurrentIndex(column_indices["column"] + 1)
        except Exception:
            pass

        # Term列：优先 Term / Name / Pathway / ID
        term_idx = None
        for priority_name in ["Term", "Name", "Pathway", "Description", "ID"]:
            for i, name in enumerate(self.column_names):
                if priority_name.lower() in name.lower():
                    term_idx = i
                    break
            if term_idx is not None:
                break
        if term_idx is not None:
            self.term_column_combo.setCurrentIndex(term_idx)

        # 排序：优先 Adjusted P-value / P-value
        for preferred in ["Adjusted P-value", "P-value"]:
            idx = self.sort_by_combo.findText(preferred)
            if idx >= 0:
                self.sort_by_combo.setCurrentIndex(idx)
                break

        # 给常用控件加 tooltip，降低“Column/Hue/X含义不清晰”的困扰
        try:
            self.term_column_combo.setToolTip(self.trans.get("tip_term_column", ""))
            self.column_combo.setToolTip(self.trans.get("tip_column", ""))
            self.x_combo.setToolTip(self.trans.get("tip_x_group", ""))
            self.hue_combo.setToolTip(self.trans.get("tip_hue", ""))
            self.thresh_spin.setToolTip(self.trans.get("tip_threshold", ""))
            self.top_term_spin.setToolTip(self.trans.get("tip_top_term", ""))
            self.top_term_per_group_check.setToolTip(self.trans.get("tip_top_term_per_group", ""))
            self.sort_by_combo.setToolTip(self.trans.get("tip_sort_by", ""))
            self.sort_order_combo.setToolTip(self.trans.get("tip_sort_order", ""))
            self.min_overlap_spin.setToolTip(self.trans.get("tip_min_overlap", ""))
            self.min_gene_ratio_spin.setToolTip(self.trans.get("tip_min_gene_ratio", ""))
        except Exception:
            pass

    def _get_sort_candidates(self, columns: list[str]) -> list[str]:
        # 额外提供两个派生字段，方便 Hypergeometric 结果排序
        base = [c for c in columns]
        extra = ["Overlap (k)", "Gene Ratio (k/n)"]
        # 保持顺序：常见列靠前
        preferred = ["Adjusted P-value", "P-value", "Odds Ratio", "Combined Score", "Overlap", "Gene_set", "Term"]
        ordered: list[str] = []
        for p in preferred:
            for c in base:
                if c == p and c not in ordered:
                    ordered.append(c)
        for c in base:
            if c not in ordered:
                ordered.append(c)
        ordered.extend(extra)
        return ordered

    def _parse_overlap(self, value: object) -> tuple[int | None, int | None, float | None]:
        """Parse overlap string like '334/803' -> (k, n, k/n)."""
        if value is None or (isinstance(value, float) and pd.isna(value)):
            return None, None, None
        text = str(value).strip()
        if "/" in text:
            parts = text.split("/", 1)
            try:
                k = int(float(parts[0]))
                n = int(float(parts[1]))
                ratio = (k / n) if n else None
                return k, n, ratio
            except Exception:
                return None, None, None
        return None, None, None

    def _prepare_plot_df(self, plot_df: pd.DataFrame) -> pd.DataFrame:
        """Apply term column mapping, ORA filters and sorting before plotting."""
        df = plot_df.copy()

        # Term 列映射：gseapy 习惯使用 'Term'
        term_col = self.term_column_combo.currentText() if hasattr(self, "term_column_combo") else ""
        if term_col and term_col in df.columns and term_col != "Term":
            df["Term"] = df[term_col].astype(str)

        # Overlap 派生字段（用于过滤/排序）
        if "Overlap" in df.columns:
            parsed = df["Overlap"].apply(self._parse_overlap)
            df["__overlap_k"] = parsed.apply(lambda t: t[0] if t else None)
            df["__gene_ratio"] = parsed.apply(lambda t: t[2] if t else None)

            min_overlap = self.min_overlap_spin.value() if hasattr(self, "min_overlap_spin") else 0
            if min_overlap and min_overlap > 0:
                df = df[df["__overlap_k"].fillna(0) >= int(min_overlap)]

            min_ratio = self.min_gene_ratio_spin.value() if hasattr(self, "min_gene_ratio_spin") else 0.0
            if min_ratio and min_ratio > 0:
                df = df[df["__gene_ratio"].fillna(0) >= float(min_ratio)]

        # 排序
        sort_by = self.sort_by_combo.currentText() if hasattr(self, "sort_by_combo") else ""
        sort_order = self.sort_order_combo.currentText() if hasattr(self, "sort_order_combo") else ""
        asc_text = self.trans.get("sort_order_asc", "Ascending")
        descending = (sort_order != asc_text)

        sort_key = None
        if sort_by == "Overlap (k)" and "__overlap_k" in df.columns:
            sort_key = "__overlap_k"
        elif sort_by == "Gene Ratio (k/n)" and "__gene_ratio" in df.columns:
            sort_key = "__gene_ratio"
        elif sort_by in df.columns:
            sort_key = sort_by

        if sort_key:
            # 对 p 值列：一般是越小越显著（升序）；其它如 Odds Ratio 越大越好（降序）
            if sort_key.lower().find("p-value") >= 0 or sort_key.lower().find("pvalue") >= 0:
                effective_asc = not descending
            elif sort_key == "__overlap_k" or sort_key == "__gene_ratio":
                effective_asc = not descending
            else:
                effective_asc = not descending

            try:
                df = df.sort_values(by=sort_key, ascending=effective_asc)
            except Exception:
                pass

        # Top N：可选全局TopN（否则由 gseapy 依据 group/term 再截断）
        try:
            top_term = self.top_term_spin.value()
            per_group = self.top_term_per_group_check.isChecked()
            if not per_group and top_term and top_term > 0:
                df = df.head(int(top_term))
        except Exception:
            pass

        return df
    
    def update_plot_options(self):
        """根据绘图类型更新选项"""
        plot_type = self.plot_type_combo.currentText()
        
        if (plot_type == "Dot Plot"):
            if hasattr(self, "dot_param_section"):
                self.dot_param_section.show()
            else:
                self.dot_param_group.show()
            if hasattr(self, "bar_param_section"):
                self.bar_param_section.hide()
            else:
                self.bar_param_group.hide()
        else:  # Bar Plot
            if hasattr(self, "dot_param_section"):
                self.dot_param_section.hide()
            else:
                self.dot_param_group.hide()
            if hasattr(self, "bar_param_section"):
                self.bar_param_section.show()
            else:
                self.bar_param_group.show()

        self.update_axis_hints()

    def update_axis_hints(self, _=None):
        """在界面上明确显示当前X轴/Y轴分别来自哪一列，以及Bar Plot X值含义。"""
        if not hasattr(self, "axis_hint_label"):
            return

        plot_type = self.plot_type_combo.currentText() if hasattr(self, "plot_type_combo") else ""
        x_col = self.x_combo.currentText() if hasattr(self, "x_combo") else ""
        term_col = self.term_column_combo.currentText() if hasattr(self, "term_column_combo") else ""
        sig_col = self.column_combo.currentText() if hasattr(self, "column_combo") else ""
        hue_col = self.hue_combo.currentText() if hasattr(self, "hue_combo") else ""

        # 轴解释（尽量不依赖 gseapy 内部实现细节，只说明用户关心的列映射）
        if plot_type == "Bar Plot":
            # gseapy barplot 通常用显著性列做条形长度（常见为 -log10(p) 的尺度），Y 轴为 Term
            hint = self.trans.get("axis_hint_bar", "")
            if not hint:
                hint = (
                    "X轴：显著性数值（由 ‘{sig}’ 计算，通常是 -log10(p/FDR) 的尺度）\n"
                    "Y轴：条目名称（来自 ‘{term}’）\n"
                    "分组：按 ‘{x}’ 分组显示（图例）"
                )
            text = hint.format(sig=sig_col or "(未选)", term=term_col or "(未选)", x=x_col or "(未选)")
        else:
            hint = self.trans.get("axis_hint_dot", "")
            if not hint:
                hint = (
                    "X轴：分组类别（来自 ‘{x}’）\n"
                    "Y轴：条目名称（来自 ‘{term}’）\n"
                    "颜色/大小：由 ‘{sig}’ 控制；Hue（可选）：‘{hue}’"
                )
            text = hint.format(
                x=x_col or "(未选)",
                term=term_col or "(未选)",
                sig=sig_col or "(未选)",
                hue=hue_col or "(无)",
            )

        self.axis_hint_label.setText(text)
    
    def add_color(self):
        """添加颜色配置"""
        if self.tsv_data is None:
            return
            
        # 获取当前X/Group列的唯一值
        column_name = self.x_combo.currentText()
        if not column_name:
            return
            
        # 若通用过滤正好过滤的是 X/Group 列，则基于过滤后的取值添加颜色
        selected_values: list[str] = []
        if self._data_filter_column == column_name:
            selected_values = self.get_selected_data_filter_values()

        unique_values = selected_values if selected_values else sorted(self.tsv_data[column_name].dropna().astype(str).unique())
        
        # 检查是否已有所有值
        existing_keys = [self.color_list.item(i).text().split(':')[0] for i in range(self.color_list.count())]
        available_values = [v for v in unique_values if v not in existing_keys]
        
        if not available_values:
            QMessageBox.information(self, self.trans["msg_error"], self.trans["msg_all_colors_added"])
            return
            
        # 选择值
        value = available_values[0]
        
        # 选择颜色
        color = QColorDialog.getColor()
        if not color.isValid():
            return
            
        # 添加到列表和字典
        color_hex = color.name()
        self.colors[value] = color_hex
        self.color_list.addItem(f"{value}: {color_hex}")
        
        self.update_preview()
    
    def remove_color(self):
        """移除选中的颜色配置"""
        selected_items = self.color_list.selectedItems()
        if not selected_items:
            return
            
        for item in selected_items:
            key = item.text().split(':')[0]
            if key in self.colors:
                del self.colors[key]
            
            row = self.color_list.row(item)
            self.color_list.takeItem(row)
        
        self.update_preview()
    
    def update_preview(self):
        """更新预览（暂不实现，以避免性能问题）"""
        pass

    def get_available_mpl_styles(self):
        styles = ["default"]
        try:
            available = list(getattr(plt.style, "available", []))
            for style in sorted(set(available)):
                if style != "default":
                    styles.append(style)
        except Exception:
            # 如果环境中获取可用主题失败，至少保留default
            pass
        return styles

    def set_mpl_style(self, style: str, silent: bool = False):
        try:
            # 清理上一次主题/rcParams残余设置，再应用新主题
            plt.rcdefaults()
            plt.style.use(style)
            self.mpl_style = style
        except Exception as e:
            if not silent:
                QMessageBox.warning(
                    self,
                    self.trans["msg_error"],
                    self.trans["msg_style_apply_fail"].format(str(e)),
                )

    def on_mpl_style_changed(self, _=None):
        style = self.mpl_style_combo.currentText() if hasattr(self, "mpl_style_combo") else "default"
        if not style:
            style = "default"
        self.set_mpl_style(style, silent=False)
    
    def show_term_context_menu(self, position):
        """显示Term列表的右键菜单"""
        self.show_multi_select_context_menu(self.term_list, position)

    def show_multi_select_context_menu(self, list_widget: QListWidget, position):
        """给任意多选 QListWidget 提供全选/全不选/反选右键菜单"""
        context_menu = QMenu()
        select_all_action = context_menu.addAction(self.trans["context_select_all"])
        deselect_all_action = context_menu.addAction(self.trans["context_deselect_all"])
        invert_selection_action = context_menu.addAction(self.trans["context_invert_selection"])

        action = context_menu.exec_(list_widget.mapToGlobal(position))

        if action == select_all_action:
            self.set_all_selected(list_widget, True)
        elif action == deselect_all_action:
            self.set_all_selected(list_widget, False)
        elif action == invert_selection_action:
            self.invert_selection(list_widget)

    def set_all_selected(self, list_widget: QListWidget, selected: bool):
        for i in range(list_widget.count()):
            list_widget.item(i).setSelected(selected)

    def invert_selection(self, list_widget: QListWidget):
        for i in range(list_widget.count()):
            item = list_widget.item(i)
            item.setSelected(not item.isSelected())

    def plot_chart(self):
        """绘制图表（TSV模式）"""
        if self.tsv_data is None:
            QMessageBox.warning(self, self.trans["msg_error"], self.trans["msg_load_tsv_first"])
            return

        try:
            # 确保使用当前选择的matplotlib主题
            self.set_mpl_style(self.mpl_style, silent=True)

            plot_type = self.plot_type_combo.currentText()
            column = self.column_combo.currentText()
            x_group = self.x_combo.currentText()
            hue = self.hue_combo.currentText()
            thresh = self.thresh_spin.value()
            top_term = self.top_term_spin.value()
            figsize = (self.width_spin.value(), self.height_spin.value())
            title = self.title_edit.text()
            x_axis_fontsize = self.x_axis_fontsize_spin.value()
            y_axis_fontsize = self.y_axis_fontsize_spin.value()

            plot_df = self.tsv_data

            # 先应用“通用列过滤”（任意列 -> 多选取值）
            if self._data_filter_column and self._data_filter_column in plot_df.columns:
                selected_filter_values = self.get_selected_data_filter_values()
                if selected_filter_values:
                    plot_df = plot_df[plot_df[self._data_filter_column].astype(str).isin(selected_filter_values)]
                elif self._data_filter_available_values:
                    QMessageBox.warning(
                        self,
                        self.trans["msg_error"],
                        self.trans.get(
                            "msg_no_filter_values_selected",
                            "No values selected. Please select at least one.",
                        ),
                    )
                    return

            # Hypergeometric/ORA: term列映射 + overlap过滤 + 排序/TopN
            plot_df = self._prepare_plot_df(plot_df)

            # 预定义，避免在不同分支中出现未绑定变量
            legend_position = "best"
            bbox_to_anchor = None
            legend_loc = "best"
            need_reposition_legend = False
            bar_legend_fontsize = 8
            legend_bbox_transform = None
            
            # 只获取 Bar Plot 图例位置参数
            if plot_type == "Bar Plot":
                legend_position = self.bar_legend_pos_combo.currentText()
                bar_legend_fontsize = self.bar_legend_fontsize_spin.value() if hasattr(self, "bar_legend_fontsize_spin") else 8

            # 重要：不要先创建一张空fig再draw它。
            # 在不同版本 gseapy 中，dotplot/barplot 可能会忽略传入的ax/figsize并自行创建新figure。
            # 这会造成“只看到坐标轴但内容空白”（我们展示的是空的那张）。
            # 这里改为：优先信任 gseapy 返回的 Axes/Figure，并用 Qt 内嵌方式显示。
            ax: Axes | None = None
            fig: Figure | None = None

            if plot_type == "Dot Plot":
                dot_scale = self.dot_scale_spin.value()
                marker = self.marker_combo.currentText()
                cmap = self.cmap_combo.currentText()
                show_ring = self.show_ring_check.isChecked()
                xticklabels_rot = self.xticklabels_rot_spin.value()

                result = dotplot(
                    plot_df,
                    column=column,
                    x=x_group,
                    hue=(hue if hue else None),
                    cutoff=thresh,
                    top_term=top_term,
                    size=dot_scale,
                    title=title,
                    xticklabels_rot=xticklabels_rot,
                    show_ring=show_ring,
                    marker=marker,
                    cmap=cmap,
                )
            else:  # Bar Plot
                color_dict = self.colors if self.colors else None

                # 对barplot的调用，直接传递legend位置参数
                if legend_position == "right":
                    bbox_to_anchor = (1, 0.5)
                    legend_loc = "center left"
                elif legend_position == "center left":
                    # 放到整张图最左侧，避免覆盖y轴长标签
                    bbox_to_anchor = (0.01, 0.5)
                    legend_loc = "center left"
                    legend_bbox_transform = "figure"
                elif legend_position == "center right":
                    bbox_to_anchor = (0.99, 0.5)
                    legend_loc = "center right"
                    legend_bbox_transform = "figure"
                elif legend_position == "lower center":
                    bbox_to_anchor = (0.5, 0.01)
                    legend_loc = "lower center"
                    legend_bbox_transform = "figure"
                elif legend_position == "upper center":
                    bbox_to_anchor = (0.5, 0.99)
                    legend_loc = "upper center"
                    legend_bbox_transform = "figure"
                else:  # best
                    bbox_to_anchor = None
                    legend_loc = "best"

                with warnings.catch_warnings():
                    # gseapy 内部对 pandas groupby.apply 的用法会触发 FutureWarning；这里局部静默避免干扰用户。
                    warnings.simplefilter("ignore", FutureWarning)
                    result = barplot(
                        plot_df,
                        column=column,
                        group=x_group,
                        top_term=top_term,
                        cutoff=thresh,
                        title=title,
                        color=color_dict,
                    )
                need_reposition_legend = bool(bbox_to_anchor)

            # 兼容：gseapy 返回 Axes 或 Figure（不同版本可能不同）
            if result is None:
                raise RuntimeError("gseapy plotting returned None")
            if isinstance(result, Axes):
                ax = result
                maybe_fig = ax.get_figure()
                if isinstance(maybe_fig, Figure):
                    fig = maybe_fig
                elif isinstance(maybe_fig, SubFigure) and isinstance(getattr(maybe_fig, "figure", None), Figure):
                    fig = maybe_fig.figure
                else:
                    fig = None
            elif isinstance(result, Figure):
                fig = result
                ax = fig.axes[0] if fig.axes else None
            else:
                # 兜底：尽量从对象上取出 figure/axes
                if hasattr(result, "get_figure"):
                    ax = result  # type: ignore[assignment]
                    fig = result.get_figure()  # type: ignore[assignment]
                elif hasattr(result, "axes"):
                    fig = result  # type: ignore[assignment]
                    ax = result.axes[0] if result.axes else None  # type: ignore[attr-defined]

            if fig is None or ax is None:
                raise RuntimeError("Unable to resolve figure/axes from gseapy plot result")

            # Bar Plot：在 ax 解析出来之后再重设图例位置
            if plot_type == "Bar Plot" and need_reposition_legend and bbox_to_anchor:
                lgd = ax.get_legend()
                # 关键：优先复用 gseapy 已生成的 legend 内容。
                # 直接从 axes 推断 handles/labels 可能会拿到错误项（例如 p_inv）。
                handles: list = []
                labels: list[str] = []
                legend_title: str = ""

                if lgd is not None:
                    try:
                        legend_title = lgd.get_title().get_text() if lgd.get_title() else ""
                    except Exception:
                        legend_title = ""

                    # matplotlib 不同版本属性名不同：legendHandles / legend_handles
                    try:
                        if hasattr(lgd, "legend_handles") and getattr(lgd, "legend_handles"):
                            handles = list(getattr(lgd, "legend_handles"))
                        elif hasattr(lgd, "legendHandles") and getattr(lgd, "legendHandles"):
                            handles = list(getattr(lgd, "legendHandles"))
                    except Exception:
                        handles = []

                    try:
                        labels = [t.get_text() for t in lgd.get_texts()]
                    except Exception:
                        labels = []

                # 兜底：如果 legend 对象没给到内容，再从 axes 获取（但可能不可靠）
                if not handles or not labels:
                    try:
                        handles, labels = ax.get_legend_handles_labels()
                    except Exception:
                        handles, labels = [], []

                # 清洗掉 matplotlib 的内部/空标签
                cleaned: list[tuple[object, str]] = []
                for handle, label_text in zip(handles, labels):
                    if not label_text or str(label_text).startswith("_"):
                        continue
                    cleaned.append((handle, str(label_text)))

                # 避免出现 gseapy 内部字段（常见为 p_inv）污染 legend
                if len(cleaned) > 1:
                    cleaned = [(handle, label_text) for (handle, label_text) in cleaned if label_text != "p_inv"]

                handles = [h for (h, _l) in cleaned]
                labels = [_l for (_h, _l) in cleaned]

                if lgd is not None:
                    try:
                        lgd.remove()
                    except Exception:
                        pass

                if handles and labels:
                    legend_kwargs: dict[str, object] = {
                        "loc": legend_loc,
                        "bbox_to_anchor": bbox_to_anchor,
                        "fontsize": bar_legend_fontsize,
                    }
                    # 使用 figure 坐标把图例放到整张图边缘
                    if legend_bbox_transform == "figure" and fig is not None:
                        legend_kwargs["bbox_transform"] = fig.transFigure
                    if legend_title:
                        legend_kwargs["title"] = legend_title
                        legend_kwargs["title_fontsize"] = bar_legend_fontsize
                    ax.legend(handles, labels, **legend_kwargs)

            # 按用户设置强制figsize（直接改figure尺寸比传figsize给gseapy更稳定）
            try:
                fig.set_size_inches(figsize[0], figsize[1], forward=True)
            except Exception:
                pass

            # 设置轴标签字体大小
            ax.xaxis.label.set_size(x_axis_fontsize)
            ax.yaxis.label.set_size(y_axis_fontsize)
            # 设置x轴刻度字体大小
            ax.tick_params(axis='x', labelsize=x_axis_fontsize-2)  
            # 设置y轴刻度字体大小
            ax.tick_params(axis='y', labelsize=y_axis_fontsize-2)
            
            # 调整布局以适应图例
            if plot_type == "Bar Plot" and bbox_to_anchor:
                fig.tight_layout()
                # 为不同方向的外置图例留空间，避免覆盖长标签
                if legend_position in ("right", "center right"):
                    try:
                        fig.subplots_adjust(right=min(fig.subplotpars.right, 0.78))
                    except Exception:
                        plt.subplots_adjust(right=0.78)
                elif legend_position == "center left":
                    try:
                        fig.subplots_adjust(left=max(fig.subplotpars.left, 0.55))
                    except Exception:
                        plt.subplots_adjust(left=0.55)
                elif legend_position == "lower center":
                    try:
                        fig.subplots_adjust(bottom=max(fig.subplotpars.bottom, 0.18))
                    except Exception:
                        plt.subplots_adjust(bottom=0.18)
                elif legend_position == "upper center":
                    try:
                        fig.subplots_adjust(top=min(fig.subplotpars.top, 0.85))
                    except Exception:
                        plt.subplots_adjust(top=0.85)
            else:
                fig.tight_layout()

            self._show_figure_in_window(fig, "TSV Plot")

        except Exception as e:
            QMessageBox.critical(self, self.trans["msg_plot_error"], f"{self.trans['msg_plot_error']}: {str(e)}")
            import traceback
            traceback.print_exc()  # 添加这行来打印详细错误信息
            plt.close('all')

    def plot_gsea(self):
        """绘制GSEA图形（PKL模式）"""
        if self.gsea_result is None:
            QMessageBox.warning(self, self.trans["msg_error"], self.trans["msg_load_pkl_first"])
            return
            
        _prev_font_size = None
        try:
            # 确保使用当前选择的matplotlib主题
            self.set_mpl_style(self.mpl_style, silent=True)

            # 获取选中的Term
            selected_items = self.term_list.selectedItems()
            if not selected_items:
                QMessageBox.warning(self, self.trans["msg_error"], self.trans["msg_select_term"])
                return
                
            selected_terms = [item.text() for item in selected_items]
            show_ranking = self.show_ranking_check.isChecked()
            
            # 获取自定义图像尺寸和字体大小
            gsea_figsize = (self.gsea_width_spin.value(), self.gsea_height_spin.value())
            gsea_fontsize = self.gsea_fontsize_spin.value()
            gsea_legend_position = self.gsea_legend_pos_combo.currentText()
            gsea_legend_fontsize = self.gsea_legend_fontsize_spin.value()
            gsea_legend_outside = self.gsea_legend_outside_check.isChecked()
            
            # 准备图例位置参数
            legend_kws: dict[str, object] = {'fontsize': gsea_legend_fontsize}
            
            if gsea_legend_outside:
                # 图例放在图外
                if gsea_legend_position == "right":
                    legend_kws.update({'loc': 'center left', 'bbox_to_anchor': (1, 0.5)})
                elif gsea_legend_position == "center left":
                    legend_kws.update({'loc': 'center right', 'bbox_to_anchor': (0, 0.5)})
                elif gsea_legend_position == "center right":
                    legend_kws.update({'loc': 'center left', 'bbox_to_anchor': (1, 0.5)})
                elif gsea_legend_position == "lower center":
                    legend_kws.update({'loc': 'upper center', 'bbox_to_anchor': (0.5, 0)})
                elif gsea_legend_position == "upper center":
                    legend_kws.update({'loc': 'lower center', 'bbox_to_anchor': (0.5, 1)})
                else:  # best 或其他
                    legend_kws.update({'loc': 'center left', 'bbox_to_anchor': (1, 0.5)})
            else:
                # 图例放在图内
                legend_kws.update({'loc': gsea_legend_position})
            
            # 设置matplotlib字体大小（并在结束后恢复）
            _prev_font_size = plt.rcParams.get('font.size')
            plt.rcParams.update({'font.size': gsea_fontsize})
            
            # 关闭已存在的图形窗口
            plt.close('all')
            
            # 直接调用gsea_result.plot方法，它会返回一个figure对象
            fig = self.gsea_result.plot(
                selected_terms, 
                show_ranking=show_ranking, 
                legend_kws=legend_kws,
                figsize=gsea_figsize
            )
            
            # 为所有子图设置字体大小
            for ax in fig.get_axes():
                ax.tick_params(axis='both', labelsize=gsea_fontsize)
                for label in ax.get_xticklabels() + ax.get_yticklabels():
                    label.set_fontsize(gsea_fontsize)
                
                # 确保图例字体大小正确
                if ax.get_legend():
                    for text in ax.get_legend().get_texts():
                        text.set_fontsize(gsea_legend_fontsize)
                
                # 设置轴标签和文本字体大小
                if ax.get_xlabel():
                    ax.xaxis.label.set_size(gsea_fontsize)
                if ax.get_ylabel():
                    ax.yaxis.label.set_size(gsea_fontsize)
                for text in ax.texts:
                    text.set_fontsize(gsea_fontsize)
            
            # 创建一个新的窗口来显示这个figure
            gsea_window = QMainWindow()
            gsea_window.setWindowTitle("GSEA Plot")
            gsea_window.resize(1200, 800)  # 增加窗口尺寸，为图例留出更多空间
            
            # 创建Qt控件和布局
            central_widget = QWidget()
            gsea_window.setCentralWidget(central_widget)
            layout = QVBoxLayout(central_widget)
            
            # 将figure转换为Qt可用的canvas
            canvas = FigureCanvas(fig)
            
            # 添加导航工具栏
            toolbar = NavigationToolbar(canvas, gsea_window)
            layout.addWidget(toolbar)
            layout.addWidget(canvas)
            
            # 应用布局调整，为图例留出空间
            if gsea_legend_outside:
                fig.tight_layout()
                plt.subplots_adjust(right=0.85)
            else:
                fig.tight_layout()
                
            canvas.draw()
            
            # 显示窗口
            gsea_window.show()
            
            # 保持窗口引用
            self._gsea_window = gsea_window
            
            # 恢复默认字体大小设置
            if _prev_font_size is not None:
                plt.rcParams.update({'font.size': _prev_font_size})
            else:
                plt.rcParams.update({'font.size': matplotlib.rcParamsDefault['font.size']})
                
        except Exception as e:
            QMessageBox.critical(self, self.trans["msg_plot_error"], f"{self.trans['msg_plot_error']}: {str(e)}")
            import traceback
            traceback.print_exc()
            plt.close('all')
            # 恢复默认字体大小设置
            try:
                if _prev_font_size is not None:
                    plt.rcParams.update({'font.size': _prev_font_size})
                else:
                    plt.rcParams.update({'font.size': matplotlib.rcParamsDefault['font.size']})
            except Exception:
                pass


class XValueFilterDialog(QDialog):
    def __init__(
        self,
        parent: QWidget,
        title: str,
        values: list[str],
        selected_values: set[str],
        trans: dict,
        empty_selection_message: str | None = None,
    ):
        super().__init__(parent)
        self._values = values
        self._selected_values = set(selected_values)
        self._trans = trans
        self._empty_selection_message = empty_selection_message

        self.setWindowTitle(title)
        self.resize(520, 520)

        layout = QVBoxLayout(self)

        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText(self._trans.get("x_value_filter_search", "Search..."))
        self.search_edit.textChanged.connect(self.apply_filter)
        layout.addWidget(self.search_edit)

        self.list_widget = QListWidget()
        # checklist 样式：通过 checkState 选择，不使用高亮选择
        self.list_widget.setSelectionMode(QAbstractItemView.NoSelection)
        self.list_widget.setContextMenuPolicy(Qt.CustomContextMenu)
        self.list_widget.customContextMenuRequested.connect(self.show_checklist_context_menu)
        layout.addWidget(self.list_widget, 1)

        btn_row = QHBoxLayout()
        select_all_btn = QPushButton(self._trans.get("select_all", "Select All"))
        select_all_btn.clicked.connect(lambda: self.set_all_checked(True))
        deselect_all_btn = QPushButton(self._trans.get("deselect_all", "Deselect All"))
        deselect_all_btn.clicked.connect(lambda: self.set_all_checked(False))
        invert_btn = QPushButton(self._trans.get("invert_selection", "Invert"))
        invert_btn.clicked.connect(self.invert_checked)
        btn_row.addWidget(select_all_btn)
        btn_row.addWidget(deselect_all_btn)
        btn_row.addWidget(invert_btn)
        layout.addLayout(btn_row)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.on_accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

        self.populate()

    def populate(self):
        self.list_widget.blockSignals(True)
        self.list_widget.clear()
        # 恢复勾选；若为空则默认全勾选
        default_check_all = not self._selected_values
        for v in self._values:
            item = QListWidgetItem(v)
            item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
            if default_check_all or v in self._selected_values:
                item.setCheckState(Qt.Checked)
            else:
                item.setCheckState(Qt.Unchecked)
            self.list_widget.addItem(item)
        self.list_widget.blockSignals(False)

    def apply_filter(self, text: str):
        needle = (text or "").strip().lower()
        for i in range(self.list_widget.count()):
            item = self.list_widget.item(i)
            item.setHidden(bool(needle) and needle not in item.text().lower())

    def show_checklist_context_menu(self, position):
        context_menu = QMenu()
        check_all_action = context_menu.addAction(self._trans.get("context_select_all", "Select All"))
        uncheck_all_action = context_menu.addAction(self._trans.get("context_deselect_all", "Deselect All"))
        invert_action = context_menu.addAction(self._trans.get("context_invert_selection", "Invert Selection"))

        action = context_menu.exec_(self.list_widget.mapToGlobal(position))
        if action == check_all_action:
            self.set_all_checked(True)
        elif action == uncheck_all_action:
            self.set_all_checked(False)
        elif action == invert_action:
            self.invert_checked()

    def set_all_checked(self, checked: bool):
        state = Qt.Checked if checked else Qt.Unchecked
        for i in range(self.list_widget.count()):
            self.list_widget.item(i).setCheckState(state)

    def invert_checked(self):
        for i in range(self.list_widget.count()):
            item = self.list_widget.item(i)
            item.setCheckState(Qt.Unchecked if item.checkState() == Qt.Checked else Qt.Checked)

    def on_accept(self):
        checked = [
            self.list_widget.item(i).text()
            for i in range(self.list_widget.count())
            if self.list_widget.item(i).checkState() == Qt.Checked
        ]
        if not checked:
            QMessageBox.warning(
                self,
                self._trans.get("msg_error", "Error"),
                self._empty_selection_message
                or self._trans.get("msg_no_x_values_selected", "No values selected. Please select at least one."),
            )
            return
        self._selected_values = set(checked)
        self.accept()

    def get_selected_values(self) -> list[str]:
        return sorted(self._selected_values)


def main():
    app = QApplication.instance()
    created_app = app is None
    if created_app:
        app = QApplication(sys.argv)
    window = GSEAVisualizationGUI()
    window.show()
    return app.exec_() if created_app else 0


if __name__ == "__main__":
    sys.exit(main())