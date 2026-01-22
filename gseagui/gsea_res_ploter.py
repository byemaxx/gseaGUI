import sys
import pandas as pd
import pickle
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
                             QListWidgetItem)
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
        fit_window_to_available_screen(self, 1200, 800)
        
        # 数据存储
        self.tsv_data = None
        self.gsea_result = None
        self.current_file_type = None
        self.column_names = []
        self.colors = {}
        self.mpl_style = "default"

        # TSV: X/Group 值筛选状态
        self._x_filter_column: str | None = None
        self._x_filter_selected_values: set[str] = set()
        self._x_filter_available_values: list[str] = []
        
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
        
        # 绘图类型
        plot_type_group = QGroupBox(self.trans["plot_type_group"])
        plot_type_layout = QVBoxLayout(plot_type_group)
        
        self.plot_type_combo = QComboBox()
        self.plot_type_combo.addItems(["Dot Plot", "Bar Plot"])
        self.plot_type_combo.currentIndexChanged.connect(self.update_plot_options)
        plot_type_layout.addWidget(self.plot_type_combo)
        
        tsv_layout.addWidget(plot_type_group)
        
        # 基本参数
        basic_param_group = QGroupBox(self.trans["basic_param_group"])
        basic_param_layout = QGridLayout(basic_param_group)
        
        basic_param_layout.addWidget(QLabel(self.trans["column"]), 0, 0)
        self.column_combo = QComboBox()
        self.column_combo.currentIndexChanged.connect(self.update_preview)
        basic_param_layout.addWidget(self.column_combo, 0, 1)
        
        basic_param_layout.addWidget(QLabel(self.trans["x_group"]), 1, 0)
        self.x_combo = QComboBox()
        self.x_combo.currentIndexChanged.connect(self.update_preview)
        self.x_combo.currentIndexChanged.connect(self.on_x_column_changed)

        x_group_container = QWidget()
        x_group_v = QVBoxLayout(x_group_container)
        x_group_v.setContentsMargins(0, 0, 0, 0)
        x_group_v.setSpacing(2)

        x_group_h = QHBoxLayout()
        x_group_h.setContentsMargins(0, 0, 0, 0)
        x_group_h.addWidget(self.x_combo, 1)
        self.x_filter_btn = QPushButton(self.trans["x_value_filter_btn"])
        self.x_filter_btn.clicked.connect(self.open_x_value_filter_dialog)
        self.x_filter_btn.setEnabled(False)
        x_group_h.addWidget(self.x_filter_btn, 0)
        x_group_v.addLayout(x_group_h)

        self.x_filter_status_label = QLabel("")
        self.x_filter_status_label.setStyleSheet("color: #666666; font-size: 11px;")
        x_group_v.addWidget(self.x_filter_status_label)

        basic_param_layout.addWidget(x_group_container, 1, 1)
        
        basic_param_layout.addWidget(QLabel(self.trans["hue"]), 2, 0)
        self.hue_combo = QComboBox()
        self.hue_combo.currentIndexChanged.connect(self.update_preview)
        basic_param_layout.addWidget(self.hue_combo, 2, 1)
        
        basic_param_layout.addWidget(QLabel(self.trans["threshold"]), 3, 0)
        self.thresh_spin = QDoubleSpinBox()
        self.thresh_spin.setRange(0, 1)
        self.thresh_spin.setDecimals(3)
        self.thresh_spin.setSingleStep(0.001)
        self.thresh_spin.setValue(0.05)
        self.thresh_spin.valueChanged.connect(self.update_preview)
        basic_param_layout.addWidget(self.thresh_spin, 3, 1)
        
        basic_param_layout.addWidget(QLabel(self.trans["top_term"]), 4, 0)
        self.top_term_spin = QSpinBox()
        self.top_term_spin.setRange(1, 100)
        self.top_term_spin.setValue(5)
        self.top_term_spin.valueChanged.connect(self.update_preview)
        basic_param_layout.addWidget(self.top_term_spin, 4, 1)
        
        basic_param_layout.addWidget(QLabel(self.trans["img_size"]), 5, 0)
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
        basic_param_layout.addLayout(size_layout, 5, 1)
        
        basic_param_layout.addWidget(QLabel(self.trans["title"]), 6, 0)
        self.title_edit = QLineEdit("")
        basic_param_layout.addWidget(self.title_edit, 6, 1)
        
        # 在基本参数组中添加轴标签字体大小设置
        basic_param_layout.addWidget(QLabel(self.trans["x_axis_fontsize"]), 7, 0)
        self.x_axis_fontsize_spin = QSpinBox()
        self.x_axis_fontsize_spin.setRange(5, 24)
        self.x_axis_fontsize_spin.setValue(14)
        basic_param_layout.addWidget(self.x_axis_fontsize_spin, 7, 1)
        
        basic_param_layout.addWidget(QLabel(self.trans["y_axis_fontsize"]), 8, 0)
        self.y_axis_fontsize_spin = QSpinBox()
        self.y_axis_fontsize_spin.setRange(5, 24)
        self.y_axis_fontsize_spin.setValue(14)
        basic_param_layout.addWidget(self.y_axis_fontsize_spin, 8, 1)

        # Matplotlib主题/样式
        basic_param_layout.addWidget(QLabel(self.trans["mpl_style"]), 9, 0)
        self.mpl_style_combo = QComboBox()
        self.mpl_style_combo.addItems(self.get_available_mpl_styles())
        self.mpl_style_combo.setCurrentText(self.mpl_style)
        self.mpl_style_combo.currentIndexChanged.connect(self.on_mpl_style_changed)
        basic_param_layout.addWidget(self.mpl_style_combo, 9, 1)
        
        tsv_layout.addWidget(basic_param_group)

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
        
        tsv_layout.addWidget(self.dot_param_group)
        
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
        
        tsv_layout.addWidget(self.bar_param_group)
        self.bar_param_group.hide()  # 初始隐藏
        
        # 绘图按钮
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
            
            self.column_combo.addItems(self.column_names)
            self.x_combo.addItems(self.column_names)
            self.hue_combo.addItems(self.column_names)
            
            # 预设常见值（如果存在）
            self.set_default_columns()

            # 根据当前 X/Group 列刷新可选组（默认全选）
            self.refresh_x_value_filter(reset_selection=True)
            
            # 启用TSV选项卡
            self.tab_widget.setTabEnabled(0, True)
            self.tab_widget.setTabEnabled(1, False)
            self.tab_widget.setCurrentIndex(0)
            
            QMessageBox.information(self, self.trans["msg_load_success"], self.trans["msg_tsv_loaded"].format(len(self.tsv_data)))
            
        except Exception as e:
            QMessageBox.critical(self, self.trans["msg_load_fail"], f"{self.trans['msg_load_fail']}: {str(e)}")
    
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
        if "column" in column_indices:
            self.hue_combo.setCurrentIndex(column_indices["column"])
    
    def update_plot_options(self):
        """根据绘图类型更新选项"""
        plot_type = self.plot_type_combo.currentText()
        
        if (plot_type == "Dot Plot"):
            self.dot_param_group.show()
            self.bar_param_group.hide()
        else:  # Bar Plot
            self.dot_param_group.hide()
            self.bar_param_group.show()
    
    def add_color(self):
        """添加颜色配置"""
        if not self.tsv_data is not None:
            return
            
        # 获取当前X/Group列的唯一值
        column_name = self.x_combo.currentText()
        if not column_name:
            return
            
        # 优先基于当前筛选的值添加颜色，避免出现“画不到的组”
        selected_values = self.get_selected_x_values()
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

    def on_x_column_changed(self, _=None):
        self.refresh_x_value_filter(reset_selection=True)

    def refresh_x_value_filter(self, reset_selection: bool = False):
        """刷新 X/Group 列的可选值列表（默认全选）。"""
        if self.tsv_data is None:
            return

        column_name = self.x_combo.currentText() if hasattr(self, "x_combo") else ""
        if not column_name or column_name not in self.tsv_data.columns:
            self._x_filter_column = None
            self._x_filter_selected_values = set()
            self._x_filter_available_values = []
            if hasattr(self, "x_filter_btn"):
                self.x_filter_btn.setEnabled(False)
            self.update_x_filter_status_label()
            return

        # 取得唯一值（转成 str，保证和 QListWidget 的文本一致）
        values = (
            self.tsv_data[column_name]
            .dropna()
            .astype(str)
            .unique()
            .tolist()
        )
        values = sorted(values)
        self._x_filter_available_values = values

        # 是否需要重置选择（列变化或外部要求）
        column_changed = (self._x_filter_column != column_name)
        if column_changed:
            self._x_filter_column = column_name
            self._x_filter_selected_values = set()
            reset_selection = True

        if reset_selection or not self._x_filter_selected_values:
            self._x_filter_selected_values = set(values)
        else:
            self._x_filter_selected_values = self._x_filter_selected_values.intersection(values)

        if hasattr(self, "x_filter_btn"):
            self.x_filter_btn.setEnabled(True)
        self.update_x_filter_status_label()

    def update_x_filter_status_label(self):
        if not hasattr(self, "x_filter_status_label"):
            return
        if not self._x_filter_column:
            self.x_filter_status_label.setText("")
            return
        total = len(self._x_filter_available_values)
        selected = len(self._x_filter_selected_values)
        if total == 0:
            self.x_filter_status_label.setText(self.trans.get("x_value_filter_status_empty", ""))
        elif selected == total:
            self.x_filter_status_label.setText(self.trans["x_value_filter_status_all"].format(total))
        else:
            self.x_filter_status_label.setText(self.trans["x_value_filter_status_some"].format(selected, total))

    def open_x_value_filter_dialog(self):
        if self.tsv_data is None:
            QMessageBox.warning(self, self.trans["msg_error"], self.trans["msg_load_tsv_first"])
            return

        # 确保缓存是最新的
        self.refresh_x_value_filter(reset_selection=False)
        if not self._x_filter_column:
            return

        dlg = XValueFilterDialog(
            parent=self,
            title=self.trans["x_value_filter_dialog_title"].format(self._x_filter_column),
            values=self._x_filter_available_values,
            selected_values=self._x_filter_selected_values,
            trans=self.trans,
        )
        if dlg.exec_() == QDialog.Accepted:
            self._x_filter_selected_values = set(dlg.get_selected_values())
            self.update_x_filter_status_label()
            self.update_preview()

    def get_selected_x_values(self) -> list[str]:
        if self.tsv_data is None:
            return []
        if not self._x_filter_column:
            return []
        if not self._x_filter_selected_values:
            return []
        return sorted(self._x_filter_selected_values)

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

            # 应用 X/Group 值筛选（只绘制选中的组）
            plot_df = self.tsv_data
            selected_x_values = self.get_selected_x_values()
            if selected_x_values and x_group in plot_df.columns:
                plot_df = plot_df[plot_df[x_group].astype(str).isin(selected_x_values)]
            elif self._x_filter_column == x_group and self._x_filter_available_values and not selected_x_values:
                QMessageBox.warning(self, self.trans["msg_error"], self.trans["msg_no_x_values_selected"])
                return

            # 预定义，避免在不同分支中出现未绑定变量
            legend_position = "best"
            bbox_to_anchor = None
            legend_loc = "best"
            need_reposition_legend = False
            
            # 只获取 Bar Plot 图例位置参数
            if plot_type == "Bar Plot":
                legend_position = self.bar_legend_pos_combo.currentText()

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
                    hue=hue,
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
                    bbox_to_anchor = (0, 0.5)
                    legend_loc = "center right"
                elif legend_position == "center right":
                    bbox_to_anchor = (1, 0.5)
                    legend_loc = "center left"
                elif legend_position == "lower center":
                    bbox_to_anchor = (0.5, 0)
                    legend_loc = "upper center"
                elif legend_position == "upper center":
                    bbox_to_anchor = (0.5, 1)
                    legend_loc = "lower center"
                else:  # best
                    bbox_to_anchor = None
                    legend_loc = "best"
                
                # 直接修改传给barplot调用的参数
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
                if lgd is not None:
                    handles = lgd.legendHandles
                    labels = [t.get_text() for t in lgd.get_texts()]
                    lgd.remove()
                    ax.legend(handles, labels, loc=legend_loc, bbox_to_anchor=bbox_to_anchor)

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
                if legend_position == "right":
                    plt.subplots_adjust(right=0.8)
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
    def __init__(self, parent: QWidget, title: str, values: list[str], selected_values: set[str], trans: dict):
        super().__init__(parent)
        self._values = values
        self._selected_values = set(selected_values)
        self._trans = trans

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
                self._trans.get("msg_no_x_values_selected", ""),
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