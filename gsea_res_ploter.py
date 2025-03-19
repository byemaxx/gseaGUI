import sys
import os
import pandas as pd
import numpy as np
import pickle
import matplotlib
matplotlib.use('Qt5Agg')  # 使用Qt5Agg后端
from gseapy import barplot, dotplot
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                             QPushButton, QLabel, QComboBox, QFileDialog, QTabWidget, 
                             QSpinBox, QDoubleSpinBox, QCheckBox, QGroupBox, QListWidget,
                             QGridLayout, QLineEdit, QColorDialog, QMessageBox, QMenu)
from PyQt5.QtCore import Qt


class GSEAVisualizationGUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("GSEA可视化工具")
        self.setGeometry(100, 100, 1200, 800)
        
        # 数据存储
        self.tsv_data = None
        self.gsea_result = None
        self.current_file_type = None
        self.column_names = []
        self.colors = {}
        
        # 初始化UI
        self.init_ui()
        
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
        file_group = QGroupBox("文件加载")
        file_layout = QVBoxLayout(file_group)
        
        self.load_file_btn = QPushButton("加载文件 (TSV/PKL)")
        self.load_file_btn.clicked.connect(self.load_file)
        file_layout.addWidget(self.load_file_btn)
        
        self.file_path_label = QLabel("未加载文件")
        file_layout.addWidget(self.file_path_label)
        
        control_layout.addWidget(file_group)
        
        # 创建选项卡部件
        self.tab_widget = QTabWidget()
        
        # TSV选项卡
        self.tsv_tab = QWidget()
        tsv_layout = QVBoxLayout(self.tsv_tab)
        
        # 绘图类型
        plot_type_group = QGroupBox("绘图类型")
        plot_type_layout = QVBoxLayout(plot_type_group)
        
        self.plot_type_combo = QComboBox()
        self.plot_type_combo.addItems(["Dot Plot", "Bar Plot"])
        self.plot_type_combo.currentIndexChanged.connect(self.update_plot_options)
        plot_type_layout.addWidget(self.plot_type_combo)
        
        tsv_layout.addWidget(plot_type_group)
        
        # 基本参数
        basic_param_group = QGroupBox("基本参数")
        basic_param_layout = QGridLayout(basic_param_group)
        
        basic_param_layout.addWidget(QLabel("Column:"), 0, 0)
        self.column_combo = QComboBox()
        self.column_combo.currentIndexChanged.connect(self.update_preview)
        basic_param_layout.addWidget(self.column_combo, 0, 1)
        
        basic_param_layout.addWidget(QLabel("X/Group:"), 1, 0)
        self.x_combo = QComboBox()
        self.x_combo.currentIndexChanged.connect(self.update_preview)
        basic_param_layout.addWidget(self.x_combo, 1, 1)
        
        basic_param_layout.addWidget(QLabel("Hue:"), 2, 0)
        self.hue_combo = QComboBox()
        self.hue_combo.currentIndexChanged.connect(self.update_preview)
        basic_param_layout.addWidget(self.hue_combo, 2, 1)
        
        basic_param_layout.addWidget(QLabel("阈值:"), 3, 0)
        self.thresh_spin = QDoubleSpinBox()
        self.thresh_spin.setRange(0, 1)
        self.thresh_spin.setSingleStep(0.01)
        self.thresh_spin.setValue(0.05)
        self.thresh_spin.valueChanged.connect(self.update_preview)
        basic_param_layout.addWidget(self.thresh_spin, 3, 1)
        
        basic_param_layout.addWidget(QLabel("Top Term:"), 4, 0)
        self.top_term_spin = QSpinBox()
        self.top_term_spin.setRange(1, 100)
        self.top_term_spin.setValue(5)
        self.top_term_spin.valueChanged.connect(self.update_preview)
        basic_param_layout.addWidget(self.top_term_spin, 4, 1)
        
        basic_param_layout.addWidget(QLabel("图像尺寸:"), 5, 0)
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
        
        basic_param_layout.addWidget(QLabel("标题:"), 6, 0)
        self.title_edit = QLineEdit("")
        basic_param_layout.addWidget(self.title_edit, 6, 1)
        
        # 在基本参数组中添加轴标签字体大小设置
        basic_param_layout.addWidget(QLabel("X轴标签字体大小:"), 7, 0)
        self.x_axis_fontsize_spin = QSpinBox()
        self.x_axis_fontsize_spin.setRange(8, 24)
        self.x_axis_fontsize_spin.setValue(14)
        basic_param_layout.addWidget(self.x_axis_fontsize_spin, 7, 1)
        
        basic_param_layout.addWidget(QLabel("Y轴标签字体大小:"), 8, 0)
        self.y_axis_fontsize_spin = QSpinBox()
        self.y_axis_fontsize_spin.setRange(8, 24)
        self.y_axis_fontsize_spin.setValue(14)
        basic_param_layout.addWidget(self.y_axis_fontsize_spin, 8, 1)
        
        tsv_layout.addWidget(basic_param_group)
        
        # Dot Plot特定参数
        self.dot_param_group = QGroupBox("Dot Plot参数")
        dot_param_layout = QGridLayout(self.dot_param_group)
        
        dot_param_layout.addWidget(QLabel("点大小缩放:"), 0, 0)
        self.dot_scale_spin = QDoubleSpinBox()
        self.dot_scale_spin.setRange(1, 20)
        self.dot_scale_spin.setValue(3)
        self.dot_scale_spin.valueChanged.connect(self.update_preview)
        dot_param_layout.addWidget(self.dot_scale_spin, 0, 1)
        
        dot_param_layout.addWidget(QLabel("标记形状:"), 1, 0)
        self.marker_combo = QComboBox()
        self.marker_combo.addItems(["o", "s", "^", "D", "*", "p", "h", "8"])
        self.marker_combo.currentIndexChanged.connect(self.update_preview)
        dot_param_layout.addWidget(self.marker_combo, 1, 1)
        
        dot_param_layout.addWidget(QLabel("颜色映射:"), 2, 0)
        self.cmap_combo = QComboBox()
        self.cmap_combo.addItems(["viridis", "viridis_r", "plasma", "plasma_r", "Blues", "Blues_r", "Reds", "Reds_r"])
        self.cmap_combo.currentIndexChanged.connect(self.update_preview)
        dot_param_layout.addWidget(self.cmap_combo, 2, 1)
        
        self.show_ring_check = QCheckBox("显示外环")
        self.show_ring_check.setChecked(True)
        self.show_ring_check.stateChanged.connect(self.update_preview)
        dot_param_layout.addWidget(self.show_ring_check, 3, 0, 1, 2)
        
        dot_param_layout.addWidget(QLabel("标签旋转:"), 4, 0)
        self.xticklabels_rot_spin = QSpinBox()
        self.xticklabels_rot_spin.setRange(0, 90)
        self.xticklabels_rot_spin.setValue(45)
        self.xticklabels_rot_spin.valueChanged.connect(self.update_preview)
        dot_param_layout.addWidget(self.xticklabels_rot_spin, 4, 1)
        
        # 修改Dot Plot参数组中的legend设置 - 只保留字体大小设置
        dot_param_layout.addWidget(QLabel("图例字体大小:"), 5, 0)
        self.legend_fontsize_spin = QSpinBox()
        self.legend_fontsize_spin.setRange(6, 18)
        self.legend_fontsize_spin.setValue(10)
        dot_param_layout.addWidget(self.legend_fontsize_spin, 5, 1)
        
        # 移除图例位置和外部显示的控制选项
        
        tsv_layout.addWidget(self.dot_param_group)
        
        # Bar Plot特定参数
        self.bar_param_group = QGroupBox("Bar Plot参数")
        bar_param_layout = QVBoxLayout(self.bar_param_group)
        
        # 颜色选择
        self.color_list = QListWidget()
        self.color_list.setMaximumHeight(150)
        bar_param_layout.addWidget(self.color_list)
        
        color_btn_layout = QHBoxLayout()
        self.add_color_btn = QPushButton("添加颜色")
        self.add_color_btn.clicked.connect(self.add_color)
        self.remove_color_btn = QPushButton("移除颜色")
        self.remove_color_btn.clicked.connect(self.remove_color)
        color_btn_layout.addWidget(self.add_color_btn)
        color_btn_layout.addWidget(self.remove_color_btn)
        
        bar_param_layout.addLayout(color_btn_layout)
        
        # 在Bar Plot参数组中也只保留字体大小设置
        bar_param_layout.addWidget(QLabel("图例字体大小:"))
        self.bar_legend_fontsize_spin = QSpinBox()
        self.bar_legend_fontsize_spin.setRange(6, 18)
        self.bar_legend_fontsize_spin.setValue(6)
        bar_param_layout.addWidget(self.bar_legend_fontsize_spin)
        
        # 在 Bar Plot 参数组中添加 legend 位置设置
        bar_param_layout.addWidget(QLabel("图例位置:"))
        self.bar_legend_pos_combo = QComboBox()
        self.bar_legend_pos_combo.addItems(["right", "center left", "center right", "lower center", "upper center", "best"])
        self.bar_legend_pos_combo.setCurrentText("center right")
        bar_param_layout.addWidget(self.bar_legend_pos_combo)
        
        tsv_layout.addWidget(self.bar_param_group)
        self.bar_param_group.hide()  # 初始隐藏
        
        # 绘图按钮
        self.plot_button = QPushButton("绘制图形")
        self.plot_button.clicked.connect(self.plot_chart)
        tsv_layout.addWidget(self.plot_button)
        
        # PKL选项卡
        self.pkl_tab = QWidget()
        pkl_layout = QVBoxLayout(self.pkl_tab)
        
        # Term选择
        term_group = QGroupBox("Term选择")
        term_layout = QVBoxLayout(term_group)
        
        self.term_list = QListWidget()
        self.term_list.setSelectionMode(QListWidget.MultiSelection)
        self.term_list.setContextMenuPolicy(Qt.CustomContextMenu)  # 设置自定义上下文菜单
        self.term_list.customContextMenuRequested.connect(self.show_term_context_menu)  # 连接右键菜单信号
        term_layout.addWidget(self.term_list)
        
        self.show_ranking_check = QCheckBox("显示排名")
        self.show_ranking_check.setChecked(False)
        term_layout.addWidget(self.show_ranking_check)
        
        # GSEA绘图尺寸和字体设置
        gsea_param_group = QGroupBox("绘图参数")
        gsea_param_layout = QGridLayout(gsea_param_group)
        
        gsea_param_layout.addWidget(QLabel("图像尺寸:"), 0, 0)
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
        
        gsea_param_layout.addWidget(QLabel("标签字体大小:"), 1, 0)
        self.gsea_fontsize_spin = QSpinBox()
        self.gsea_fontsize_spin.setRange(8, 20)
        self.gsea_fontsize_spin.setValue(12)
        gsea_param_layout.addWidget(self.gsea_fontsize_spin, 1, 1)
        
        # 在GSEA绘图参数中保留完整的图例设置
        gsea_param_layout.addWidget(QLabel("图例位置:"), 2, 0)
        self.gsea_legend_pos_combo = QComboBox()
        self.gsea_legend_pos_combo.addItems(["right", "center left", "center right", "lower center", "upper center", "best"])
        self.gsea_legend_pos_combo.setCurrentText("best")  # 默认为best
        gsea_param_layout.addWidget(self.gsea_legend_pos_combo, 2, 1)
        
        gsea_param_layout.addWidget(QLabel("图例字体大小:"), 3, 0)
        self.gsea_legend_fontsize_spin = QSpinBox()
        self.gsea_legend_fontsize_spin.setRange(6, 18)
        self.gsea_legend_fontsize_spin.setValue(6)  # 默认字体大小为6
        gsea_param_layout.addWidget(self.gsea_legend_fontsize_spin, 3, 1)
        
        # 添加图例位置控制选项
        gsea_param_layout.addWidget(QLabel("图例在图外:"), 4, 0)
        self.gsea_legend_outside_check = QCheckBox()
        self.gsea_legend_outside_check.setChecked(False)  # 默认在图内
        gsea_param_layout.addWidget(self.gsea_legend_outside_check, 4, 1)
        
        term_layout.addWidget(gsea_param_group)
        
        pkl_layout.addWidget(term_group)
        
        # 绘图按钮
        self.gsea_plot_button = QPushButton("绘制GSEA图形")
        self.gsea_plot_button.clicked.connect(self.plot_gsea)
        pkl_layout.addWidget(self.gsea_plot_button)
        
        # 将选项卡添加到选项卡部件
        self.tab_widget.addTab(self.tsv_tab, "TSV绘图")
        self.tab_widget.addTab(self.pkl_tab, "GSEA绘图")
        self.tab_widget.setTabEnabled(0, False)
        self.tab_widget.setTabEnabled(1, False)
        
        control_layout.addWidget(self.tab_widget)
        
        # 添加控制面板到主布局
        main_layout.addWidget(control_panel)
        
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
            QMessageBox.warning(self, "不支持的文件类型", "请选择TSV或PKL文件")
    
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
            
            # 启用TSV选项卡
            self.tab_widget.setTabEnabled(0, True)
            self.tab_widget.setTabEnabled(1, False)
            self.tab_widget.setCurrentIndex(0)
            
            QMessageBox.information(self, "加载成功", f"成功加载TSV文件，包含{len(self.tsv_data)}行数据")
            
        except Exception as e:
            QMessageBox.critical(self, "加载失败", f"加载TSV文件时出错：{str(e)}")
    
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
            
            QMessageBox.information(self, "加载成功", f"成功加载GSEA结果，包含{len(terms)}个Term")
            
        except Exception as e:
            QMessageBox.critical(self, "加载失败", f"加载PKL文件时出错：{str(e)}")
    
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
            
        unique_values = sorted(self.tsv_data[column_name].unique())
        
        # 检查是否已有所有值
        existing_keys = [self.color_list.item(i).text().split(':')[0] for i in range(self.color_list.count())]
        available_values = [v for v in unique_values if v not in existing_keys]
        
        if not available_values:
            QMessageBox.information(self, "提示", "已为所有值添加了颜色")
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
    
    def show_term_context_menu(self, position):
        """显示Term列表的右键菜单"""
        context_menu = QMenu()
        select_all_action = context_menu.addAction("全选")
        deselect_all_action = context_menu.addAction("全不选")
        invert_selection_action = context_menu.addAction("反选")
        
        action = context_menu.exec_(self.term_list.mapToGlobal(position))
        
        if action == select_all_action:
            # 全选
            for i in range(self.term_list.count()):
                self.term_list.item(i).setSelected(True)
        elif action == deselect_all_action:
            # 全不选
            for i in range(self.term_list.count()):
                self.term_list.item(i).setSelected(False)
        elif action == invert_selection_action:
            # 反选
            for i in range(self.term_list.count()):
                item = self.term_list.item(i)
                item.setSelected(not item.isSelected())

    def plot_chart(self):
        """绘制图表（TSV模式）"""
        if self.tsv_data is None:
            QMessageBox.warning(self, "错误", "请先加载TSV文件")
            return

        try:
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
            
            # 只获取 Bar Plot 图例位置参数
            if plot_type == "Bar Plot":
                legend_position = self.bar_legend_pos_combo.currentText()

            # 改用subplots创建图像和坐标轴
            fig, ax = plt.subplots(figsize=figsize)

            if plot_type == "Dot Plot":
                dot_scale = self.dot_scale_spin.value()
                marker = self.marker_combo.currentText()
                cmap = self.cmap_combo.currentText()
                show_ring = self.show_ring_check.isChecked()
                xticklabels_rot = self.xticklabels_rot_spin.value()

                ax = dotplot(
                    self.tsv_data,
                    column=column,
                    x=x_group,
                    hue=hue,
                    cutoff=thresh,
                    top_term=top_term,
                    size=dot_scale,
                    figsize=figsize,
                    title=title,
                    xticklabels_rot=xticklabels_rot,
                    show_ring=show_ring,
                    marker=marker,
                    cmap=cmap,
                    ax=ax  # 显式传入坐标轴
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
                ax = barplot(
                    self.tsv_data,
                    column=column,
                    group=x_group,
                    top_term=top_term,
                    cutoff=thresh,
                    title=title,
                    figsize=figsize,
                    color=color_dict,
                    ax=ax
                )
                
                # 如果有图例并且需要自定义位置，重新设置图例
                if ax.get_legend() and bbox_to_anchor:
                    # 找到现有的图例元素
                    handles = ax.get_legend().get_lines()
                    labels = [t.get_text() for t in ax.get_legend().get_texts()]
                    
                    # 移除现有图例
                    ax.get_legend().remove()
                    
                    # 创建新图例，位置在图外
                    ax.legend(
                        handles, 
                        labels, 
                        loc=legend_loc, 
                        bbox_to_anchor=bbox_to_anchor
                    )

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
                
            fig.canvas.draw()
            plt.show(block=False)

        except Exception as e:
            QMessageBox.critical(self, "绘图错误", f"绘制图形时发生错误：{str(e)}")
            import traceback
            traceback.print_exc()  # 添加这行来打印详细错误信息
            plt.close('all')
    
    def plot_gsea(self):
        """绘制GSEA图形（PKL模式）"""
        if self.gsea_result is None:
            QMessageBox.warning(self, "错误", "请先加载GSEA结果文件（PKL）")
            return
            
        try:
            # 获取选中的Term
            selected_items = self.term_list.selectedItems()
            if not selected_items:
                QMessageBox.warning(self, "提示", "请至少选择一个Term")
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
            legend_kws = {'fontsize': gsea_legend_fontsize}
            
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
            
            # 设置matplotlib字体大小
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
            gsea_window.setWindowTitle("GSEA绘图")
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
            plt.rcParams.update({'font.size': plt.rcParamsDefault['font.size']})
                
        except Exception as e:
            QMessageBox.critical(self, "绘图错误", f"绘制GSEA图形时发生错误：{str(e)}")
            import traceback
            traceback.print_exc()
            plt.close('all')
            # 恢复默认字体大小设置
            plt.rcParams.update({'font.size': plt.rcParamsDefault['font.size']})


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = GSEAVisualizationGUI()
    window.show()
    sys.exit(app.exec_())