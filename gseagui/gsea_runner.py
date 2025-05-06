from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                           QHBoxLayout, QPushButton, QFileDialog, QLabel, 
                           QComboBox, QTextEdit, QMessageBox, QProgressDialog,
                           QCheckBox, QLineEdit, QGroupBox, QGridLayout,QSizePolicy,
                           QRadioButton, QButtonGroup, QTabWidget, QSpinBox)
# import QIntValidator
from PyQt5.QtCore import  Qt
try:
    from gseagui.enrichment_tools import EnrichmentAnalyzer
except ImportError:
    from enrichment_tools import EnrichmentAnalyzer
import sys
import os
import pandas as pd
import pickle
class EnrichmentApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.enrichment = EnrichmentAnalyzer()
        self.enrichment.set_progress_callback(self.log_progress)
        self.results = None  # 存储分析结果
        self.annotation_file_path = None  # 添加文件路径存储
        self.gene_file_path = None
        self.progress_msg = None  # 添加进度消息变量
        self.progress_dialog = None  # 添加进度对话框变量
        self.group_col_combo_1 = QComboBox(self)  # 添加group列选择控件
        self.group_col_combo_2 = QComboBox(self)  # 添加group列选择控件
        self.group_col_combo_3 = QComboBox(self)  # 添加group列选择控件
        self.save_pickle_check = QCheckBox('保存GSEA结果为pickle文件', self)
        self.save_pickle_check.setChecked(False)
        self.initUI()
        
    def initUI(self):
        self.setWindowTitle('Gene Set Enrichment Analyzer')
        self.setGeometry(100, 100, 1200, 800)
        
        # 创建中央部件和主布局
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        
        # 创建标签页
        tab_widget = QTabWidget()
        main_layout.addWidget(tab_widget)
        
        # === 第一个标签页：注释文件处理 ===
        anno_tab = QWidget()
        anno_layout = QVBoxLayout(anno_tab)
        
        # 文件选择区域
        file_group = QGroupBox("注释文件设置")
        file_layout = QVBoxLayout()
        
        # 创建标签页
        file_tab_widget = QTabWidget()
        file_layout.addWidget(file_tab_widget)
        
        # === 子标签页：注释文件 ===
        anno_file_tab = QWidget()
        anno_file_layout = QVBoxLayout(anno_file_tab)
        
        # 注释文件选择
        anno_file_select_layout = QHBoxLayout()
        self.anno_btn = QPushButton('选择注释文件', self)
        self.anno_btn.clicked.connect(self.load_annotation_file)
        self.anno_label = QLabel('未选择文件', self)
        anno_file_select_layout.addWidget(self.anno_btn)
        anno_file_select_layout.addWidget(self.anno_label)
        anno_file_layout.addLayout(anno_file_select_layout)
        
        # 列选择
        cols_layout = QGridLayout()
        self.gene_col_label = QLabel('基因/蛋白列:', self)
        self.gene_col_combo = QComboBox(self)
        self.anno_col_label = QLabel('注释列:', self)
        self.anno_col_combo = QComboBox(self)
        cols_layout.addWidget(self.gene_col_label, 0, 0)
        cols_layout.addWidget(self.gene_col_combo, 0, 1)
        cols_layout.addWidget(self.anno_col_label, 0, 2)
        cols_layout.addWidget(self.anno_col_combo, 0, 3)
        anno_file_layout.addLayout(cols_layout)
        
        # 分隔符设置
        split_layout = QHBoxLayout()
        self.split_check = QCheckBox('启用注释分割', self)
        self.split_check.setChecked(False)
        self.separator_label = QLabel('分隔符:', self)
        self.separator_input = QLineEdit(self)
        self.separator_input.setText('|')
        split_layout.addWidget(self.split_check)
        split_layout.addWidget(self.separator_label)
        split_layout.addWidget(self.separator_input)
        anno_file_layout.addLayout(split_layout)
        
        # 无效值设置
        invalid_values_layout = QHBoxLayout()
        self.invalid_values_label = QLabel('排除值 (用逗号分隔):', self)
        self.invalid_values_input = QLineEdit(self)
        self.invalid_values_input.setText('None,-,not_found,nan')
        invalid_values_layout.addWidget(self.invalid_values_label)
        invalid_values_layout.addWidget(self.invalid_values_input)
        anno_file_layout.addLayout(invalid_values_layout)
        
        # 创建基因集按钮
        self.create_gmt_btn = QPushButton('创建基因集', self)
        self.create_gmt_btn.clicked.connect(self.create_gene_sets)
        anno_file_layout.addWidget(self.create_gmt_btn)
        
        file_tab_widget.addTab(anno_file_tab, "注释文件")
        
        # === 子标签页：GMT文件 ===
        gmt_file_tab = QWidget()
        gmt_file_layout = QVBoxLayout(gmt_file_tab)
        
        # GMT文件选择
        gmt_file_select_layout = QHBoxLayout()
        self.gmt_btn = QPushButton('选择GMT文件', self)
        self.gmt_btn.clicked.connect(self.load_gmt_file)
        self.gmt_label = QLabel('未选择文件', self)
        gmt_file_select_layout.addWidget(self.gmt_btn)
        gmt_file_select_layout.addWidget(self.gmt_label)
        gmt_file_layout.addLayout(gmt_file_select_layout)
        
        file_tab_widget.addTab(gmt_file_tab, "GMT文件")
        
        file_group.setLayout(file_layout)
        anno_layout.addWidget(file_group)
        
        # === 第二个标签页：富集分析 ===
        enrich_tab = QWidget()
        enrich_layout = QVBoxLayout(enrich_tab)
        
        # 基因列表输入方式选择
        input_group = QGroupBox("基因列表输入")
        input_layout = QVBoxLayout()
        
        # 输入方式选择
        input_method_layout = QHBoxLayout()
        self.input_method_group = QButtonGroup(self)
        self.file_radio = QRadioButton("从文件输入", self)
        self.text_radio = QRadioButton("直接输入", self)
        self.file_radio.setChecked(True)
        self.input_method_group.addButton(self.file_radio)
        self.input_method_group.addButton(self.text_radio)
        input_method_layout.addWidget(self.file_radio)
        input_method_layout.addWidget(self.text_radio)
        input_layout.addLayout(input_method_layout)
        
        # 文件选择部分
        self.file_input_widget = QWidget()
        file_input_layout = QVBoxLayout(self.file_input_widget)
        
        file_select_layout = QHBoxLayout()
        self.gene_file_btn = QPushButton('选择基因列表文件', self)
        self.gene_file_btn.clicked.connect(self.load_gene_file)
        self.gene_file_label = QLabel('未选择文件', self)
        file_select_layout.addWidget(self.gene_file_btn)
        file_select_layout.addWidget(self.gene_file_label)
        file_input_layout.addLayout(file_select_layout)
        
        file_cols_layout = QHBoxLayout()
        self.gene_col_file_label = QLabel('基因列:', self)
        self.gene_col_file_combo = QComboBox(self)
        self.rank_col_label = QLabel('排序值列:', self)
        self.rank_col_combo = QComboBox(self)
        self.group_col_label_1 = QLabel('分组列_1:', self)  # 添加分组列标签
        self.group_col_label_2 = QLabel('分组列_2:', self)  # 添加分组列标签
        file_cols_layout.addWidget(self.gene_col_file_label)
        file_cols_layout.addWidget(self.gene_col_file_combo)
        file_cols_layout.addWidget(self.rank_col_label)
        file_cols_layout.addWidget(self.rank_col_combo)
        file_cols_layout.addWidget(self.group_col_label_1)  # 添加分组列标签到布局
        file_cols_layout.addWidget(self.group_col_combo_1)  # 添加分组列选择控件到布局
        file_cols_layout.addWidget(self.group_col_label_2)  # 添加分组列标签到布局
        file_cols_layout.addWidget(self.group_col_combo_2)
        self.group_col_label_3 = QLabel('分组列_3:', self)  # 添加分组列标签
        file_cols_layout.addWidget(self.group_col_label_3)  # 添加分组列标签到布局
        file_cols_layout.addWidget(self.group_col_combo_3)  # 添加分组列选择控件到布局
        file_input_layout.addLayout(file_cols_layout)
        
        # 设置尺寸策略
        self.gene_col_file_label.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Minimum)
        self.rank_col_label.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Minimum)
        self.group_col_label_1.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Minimum)
        self.group_col_label_2.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Minimum)
        self.group_col_label_3.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Minimum)
        
        self.gene_col_file_combo.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)
        self.rank_col_combo.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)
        self.group_col_combo_1.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)
        self.group_col_combo_2.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)
        self.group_col_combo_3.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)
        
        # 直接输入部分
        self.text_input_widget = QWidget()
        text_input_layout = QVBoxLayout(self.text_input_widget)
        text_input_layout.addWidget(QLabel('输入基因列表 (可选：每行"基因ID\\t排序值")：'))
        self.gene_text = QTextEdit()
        text_input_layout.addWidget(self.gene_text)
        
        # 根据选择显示不同输入方式
        self.file_radio.toggled.connect(self.file_input_widget.setVisible)
        self.text_radio.toggled.connect(self.text_input_widget.setVisible)
        
        input_layout.addWidget(self.file_input_widget)
        input_layout.addWidget(self.text_input_widget)
        self.text_input_widget.hide()
        
        input_group.setLayout(input_layout)
        enrich_layout.addWidget(input_group)
        
        # 分析方法选择
        method_group = QGroupBox("分析方法")
        method_layout = QHBoxLayout()
        self.hypergeometric_radio = QRadioButton("超几何分布", self)
        self.gsea_radio = QRadioButton("GSEA", self)
        self.hypergeometric_radio.setChecked(True)
        method_layout.addWidget(self.hypergeometric_radio)
        method_layout.addWidget(self.gsea_radio)
        
        # 添加GSEA参数设置
        self.gsea_params_widget = QWidget()
        gsea_params_layout = QHBoxLayout(self.gsea_params_widget)
        self.min_size_label = QLabel("最小基因集大小:", self)
        self.min_size_input = QSpinBox(self)
        self.min_size_input.setRange(1, 999999)
        self.min_size_input.setValue(15)
        self.max_size_label = QLabel("最大基因集大小:", self)
        self.max_size_input = QSpinBox(self)
        self.max_size_input.setRange(1, 999999)
        self.max_size_input.setValue(500)
        gsea_params_layout.addWidget(self.min_size_label)
        gsea_params_layout.addWidget(self.min_size_input)
        gsea_params_layout.addWidget(self.max_size_label)
        gsea_params_layout.addWidget(self.max_size_input)
        method_layout.addWidget(self.gsea_params_widget)
        
        # 连接单选按钮信号
        self.hypergeometric_radio.toggled.connect(self.on_method_changed)
        self.gsea_radio.toggled.connect(self.on_method_changed)
        
        # 初始隐藏GSEA参数
        self.gsea_params_widget.setVisible(False)
        
        method_group.setLayout(method_layout)
        enrich_layout.addWidget(method_group)
        
        # 输出设置
        output_group = QGroupBox("输出设置")
        output_layout = QGridLayout()
        
        # 输出目录
        self.output_dir_label = QLabel('输出目录:', self)
        self.output_dir_input = QLineEdit(self)
        self.output_dir_input.setText('enrichment_results')
        self.output_dir_btn = QPushButton('选择...', self)
        self.output_dir_btn.clicked.connect(self.select_output_dir)
        output_layout.addWidget(self.output_dir_label, 0, 0)
        output_layout.addWidget(self.output_dir_input, 0, 1)
        output_layout.addWidget(self.output_dir_btn, 0, 2)
        
        # 输出文件名前缀
        self.output_prefix_label = QLabel('输出文件名前缀:', self)
        self.output_prefix_input = QLineEdit(self)
        self.output_prefix_input.setText('enrichment')
        output_layout.addWidget(self.output_prefix_label, 1, 0)
        output_layout.addWidget(self.output_prefix_input, 1, 1)
        
        # 添加保存pickle选项
        output_layout.addWidget(self.save_pickle_check, 2, 0, 1, 3)
        
        output_group.setLayout(output_layout)
        enrich_layout.addWidget(output_group)
        
        # 移除可视化相关代码
        viz_layout = QHBoxLayout()
        enrich_layout.addLayout(viz_layout)
        
        # 运行按钮
        self.run_btn = QPushButton('运行富集分析', self)
        self.run_btn.clicked.connect(self.run_analysis)
        enrich_layout.addWidget(self.run_btn)
        

        # 将标签页添加到标签页组件
        tab_widget.addTab(anno_tab, "注释处理")
        tab_widget.addTab(enrich_tab, "富集分析")
        
        # 结果显示区域
        results_group = QGroupBox("分析结果")
        results_layout = QVBoxLayout()
        self.results_text = QTextEdit()
        self.results_text.setReadOnly(True)
        results_layout.addWidget(self.results_text)
        results_group.setLayout(results_layout)
        main_layout.addWidget(results_group)
        
        # 进度显示
        progress_group = QGroupBox("处理进度")
        progress_layout = QVBoxLayout()
        self.progress_text = QTextEdit()
        self.progress_text.setReadOnly(True)
        self.progress_text.setMaximumHeight(100)
        progress_layout.addWidget(self.progress_text)
        progress_group.setLayout(progress_layout)
        main_layout.addWidget(progress_group)
        
        # 状态栏
        self.statusBar().showMessage('就绪')
        
    def load_annotation_file(self):
        """加载注释文件"""
        fname, _ = QFileDialog.getOpenFileName(self, '选择注释文件', '', 
                                             'TSV files (*.tsv);;Text files (*.txt);;All files (*.*)')
        if fname:
            try:
                self.annotation_file_path = os.path.abspath(fname)  # 保存完整路径
                self.anno_label.setText(os.path.basename(fname))
                # 加载列名到下拉框
                columns = self.enrichment.load_annotation(self.annotation_file_path)
                self.gene_col_combo.clear()
                self.anno_col_combo.clear()
                self.gene_col_combo.addItems(columns)
                self.anno_col_combo.addItems(columns)
                self.statusBar().showMessage('注释文件加载成功')
            except Exception as e:
                QMessageBox.critical(self, '错误', f'无法加载文件: {str(e)}')
                
    def load_gene_file(self):
        """加载基因列表文件"""
        fname, _ = QFileDialog.getOpenFileName(self, '选择基因列表文件', '', 
                                             'TSV files (*.tsv);;Text files (*.txt);;All files (*.*)')
        if fname:
            try:
                self.gene_file_path = os.path.abspath(fname)  # 保存完整路径
                self.gene_file_label.setText(os.path.basename(fname))
                # 读取文件并获取列名
                df = pd.read_csv(self.gene_file_path, sep='\t')
                self.gene_col_file_combo.clear()
                self.rank_col_combo.clear()
                
                for combo in [self.group_col_combo_1, self.group_col_combo_2, self.group_col_combo_3]:
                    combo.clear()
                    combo.addItems([''] + list(df.columns))
                    
                self.gene_col_file_combo.addItems(df.columns)
                self.rank_col_combo.addItems([''] + list(df.columns))
                self.statusBar().showMessage('基因列表文件加载成功')
            except Exception as e:
                QMessageBox.critical(self, '错误', f'无法加载文件: {str(e)}')
                
    def create_gene_sets(self):
        """创建基因集"""
        if not hasattr(self.enrichment, 'df_anno') or self.enrichment.df_anno is None:
            QMessageBox.warning(self, '警告', '请先加载注释文件')
            return
            
        try:
            gene_col = self.gene_col_combo.currentText()
            anno_col = self.anno_col_combo.currentText()
            use_split = self.split_check.isChecked()
            separator = self.separator_input.text()
            invalid_values = set(x.strip() for x in self.invalid_values_input.text().split(','))

            if self.enrichment.create_gene_sets(gene_col, anno_col, use_split, separator, invalid_values):
                QMessageBox.information(self, '成功', '基因集创建成功')
                self.statusBar().showMessage('基因集创建成功')
                # 显示基因集统计信息
                self.results_text.append('基因集创建完成:')
                self.results_text.append(f'- 总通路数: {len(self.enrichment.gene_sets)}')
                total_genes = set()
                for genes in self.enrichment.gene_sets.values():
                    total_genes.update(genes)
                self.results_text.append(f'- 总基因数: {len(total_genes)}')
            else:
                QMessageBox.warning(self, '警告', '基因集创建失败')
        except Exception as e:
            QMessageBox.critical(self, '错误', f'创建基因集时出错: {str(e)}')
            
    def select_output_dir(self):
        """选择输出目录"""
        dir_name = QFileDialog.getExistingDirectory(self, '选择输出目录')
        if dir_name:
            self.output_dir_input.setText(dir_name)
            
    def log_progress(self, message):
        """添加进度消息"""
        self.progress_text.append(message)
        self.progress_text.verticalScrollBar().setValue(
            self.progress_text.verticalScrollBar().maximum()
        )
        QApplication.processEvents()

    def show_progress(self):
        """显示进度对话框"""
        self.progress_dialog = QProgressDialog("正在运行富集分析...", None, 0, 0, self)
        self.progress_dialog.setWindowTitle("进度")
        self.progress_dialog.setWindowModality(Qt.WindowModal)
        self.progress_dialog.setCancelButton(None)
        self.progress_dialog.show()
        QApplication.processEvents()

    def hide_progress(self):
        """关闭进度对话框"""
        if self.progress_dialog is not None:
            self.progress_dialog.close()
            self.progress_dialog = None
        QApplication.processEvents()

    def load_gmt_file(self):
        """加载GMT文件"""
        fname, _ = QFileDialog.getOpenFileName(self, '选择GMT文件', '', 
                                             'GMT files (*.gmt);;All files (*.*)')
        if fname:
            try:
                self.gmt_file_path = os.path.abspath(fname)  # 保存完整路径
                self.gmt_label.setText(os.path.basename(fname))
                self.enrichment.load_gmt(self.gmt_file_path)
                self.statusBar().showMessage('GMT文件加载成功')
            except Exception as e:
                QMessageBox.critical(self, '错误', f'无法加载文件: {str(e)}')

    def run_analysis(self):
        """运行富集分析"""
        if not self.enrichment.gene_sets:
            QMessageBox.warning(self, '警告', '请先创建基因集')
            return
        method = 'Hypergeometric' if self.hypergeometric_radio.isChecked() else 'GSEA'
        
        # 获取GSEA参数 - 使用value()而不是text()
        min_size = self.min_size_input.value()
        max_size = self.max_size_input.value()
        
        self.show_progress()
        try:
            # 获取输出设置
            output_dir = self.output_dir_input.text()
            output_prefix = self.output_prefix_input.text()
            
            # 创建输出目录
            if not os.path.exists(output_dir):
                os.makedirs(output_dir)
                self.log_progress(f'创建输出目录: {output_dir}')
            
            # 获取基因列表
            if self.file_radio.isChecked():
                # 从文件读取
                if not self.gene_file_path:
                    QMessageBox.warning(self, '警告', '请选择基因列表文件')
                    self.hide_progress()
                    return
                    
                self.log_progress(f'正在读取文件: {self.gene_file_path}')
                gene_col = self.gene_col_file_combo.currentText()
                rank_col = self.rank_col_combo.currentText() if self.rank_col_combo.currentText() else None
                if rank_col is None and method == 'GSEA':
                    QMessageBox.warning(self, '警告', 'GSEA方法需要排序值列')
                    self.hide_progress()
                    return
                
                group_col1 = self.group_col_combo_1.currentText() if self.group_col_combo_1.currentText() else None
                group_col2 = self.group_col_combo_2.currentText() if self.group_col_combo_2.currentText() else None
                group_col3 = self.group_col_combo_3.currentText() if self.group_col_combo_3.currentText() else None
                
                group_col_list = [group_col1, group_col2, group_col3]
                group_col_list = [col for col in group_col_list if col not in ['', None]]
                group_col_list = [x for i, x in enumerate(group_col_list) if i == group_col_list.index(x)]
                print(f'group_col_list: {group_col_list}')
                df = pd.read_csv(self.gene_file_path, sep='\t') 
                
                if len(group_col_list) == 0: # 如果没有分组列, 则直接进行富集分析
                    genes = df[gene_col].tolist()
                    if len(genes) != len(set(genes)):
                        # warning and ask if user wants to continue
                        reply = QMessageBox.question(self, '警告', '基因列表中存在重复基因，是否继续？',
                                                        QMessageBox.Yes, QMessageBox.No)
                        if reply == QMessageBox.No:
                            self.hide_progress()
                            return
                        
                        
                    rank_dict = df.set_index(gene_col)[rank_col].to_dict() if rank_col else None
                    if rank_dict is None or self.hypergeometric_radio.isChecked():
                        # 使用超几何分布
                        self.log_progress('使用超几何分布进行富集分析...')
                        results_df = self.enrichment.do_hypergeometric(genes)
                    else:
                        # 使用GSEA
                        self.log_progress('使用GSEA进行富集分析...')
                        gsea_results = self.enrichment.do_gsea(rank_dict, min_size=min_size, max_size=max_size)
                        results_df = gsea_results.res2d
                        # 根据选项保存结果对象到文件
                        if self.save_pickle_check.isChecked():
                            results_file_path = os.path.join(output_dir, f'{output_prefix}_{method}.pkl')
                            pickle.dump(gsea_results, open(results_file_path, 'wb'))
                            print(f'GSEA object saved to {results_file_path}')
                
                else: # 如果有分组列, 则按照分组列进行富集分析
                    results = []
                    def process_group(current_df, remaining_cols, group_names):
                        # 当没有剩余分组列时，对当前子 DataFrame 进行富集分析
                        if not remaining_cols:
                            sub_group_name = "~".join(group_names)
                            genes = current_df[gene_col].tolist()
                            if len(genes) != len(set(genes)):
                                reply = QMessageBox.question(self, '警告', 
                                    f'基因列表中存在重复基因，是否继续？ {sub_group_name}', 
                                    QMessageBox.Yes, QMessageBox.No)
                                if reply == QMessageBox.No:
                                    self.hide_progress()
                                    return
                            rank_dict = current_df.set_index(gene_col)[rank_col].to_dict() if rank_col else None
                            self.log_progress(f'正在分析组: {sub_group_name}')
                            if rank_dict is None or self.hypergeometric_radio.isChecked():
                                self.log_progress('使用超几何分布进行富集分析...')
                                group_results = self.enrichment.do_hypergeometric(genes)
                                if len(group_results) > 0:
                                    group_results['Gene_set'] = sub_group_name
                                else:
                                    print(f'No results for {sub_group_name}, skipping')
                                    return                                   
                                    
                            else:
                                self.log_progress('使用GSEA进行富集分析...')
                                gsea_results = self.enrichment.do_gsea(rank_dict, min_size=min_size, max_size=max_size)
                                if gsea_results is None or len(gsea_results.res2d) == 0:
                                    print(f'No results for {sub_group_name}, skipping')
                                    return
                                group_results = gsea_results.res2d
                                group_results['Name'] = sub_group_name
                                if self.save_pickle_check.isChecked():                                                       
                                    results_file_path = os.path.join(output_dir,f'{output_prefix}_GSEA_Objects', f'{output_prefix}_{sub_group_name}_{method}.pkl')
                                    pickle.dump(gsea_results, open(results_file_path, 'wb'))
                                    print(f'GSEA object saved to {results_file_path}')
                            results.append(group_results)
                        else:
                            # 当前处理的分组列
                            current_col = remaining_cols[0]
                            for group in current_df[current_col].unique():
                                filtered_df = current_df[current_df[current_col] == group]
                                process_group(filtered_df, remaining_cols[1:], group_names + [str(group)])
                    
                    if self.save_pickle_check.isChecked():
                        gsea_dir = os.path.join(output_dir, f'{output_prefix}_GSEA_Objects')
                        os.makedirs(gsea_dir, exist_ok=True)
                    
                    process_group(df, group_col_list, [])
                    results_df = pd.concat(results, ignore_index=True)
                   

            else:
                # 从文本输入读取
                text = self.gene_text.toPlainText()
                if not text.strip():
                    QMessageBox.warning(self, '警告', '请输入基因列表')
                    self.hide_progress()
                    return
                self.log_progress('正在解析输入的基因列表')
                genes, rank_dict = self.enrichment.parse_input_genes(text)
                if rank_dict is None:
                    if self.hypergeometric_radio.isChecked():
                        # 使用超几何分布
                        self.log_progress('使用超几何分布进行富集分析...')
                        results_df = self.enrichment.do_hypergeometric(genes)
                    elif self.gsea_radio.isChecked():
                        # Warning, can't use GSEA without rank values
                        QMessageBox.warning(self, '警告', 'GSEA需要排序值列')
                        self.hide_progress()
                        return
                else:
                    # 使用GSEA
                    self.log_progress('使用GSEA进行富集分析...')
                    res = self.enrichment.do_gsea(rank_dict, min_size=min_size, max_size=max_size)
                    results_df = res.res2d
                    # 根据选项保存结果对象到文件
                    if self.save_pickle_check.isChecked():
                        results_file_path = os.path.join(output_dir, f'{output_prefix}_{method}.pkl')
                        pickle.dump(res, open(results_file_path, 'wb'))
                        print(f'GSEA object saved to {results_file_path}')
            
            if results_df is not None:
                self.hide_progress()
                # 显示结果
                self.results_text.clear()
                self.results_text.append(f'使用{method}方法进行富集分析:')
                self.results_text.append('\n显著富集的前10个通路:')
                self.results_text.append(str(results_df.head(10)))
                
                # 保存结果
                output_file = os.path.join(output_dir, f'{output_prefix}_{method}.tsv')
                results_df.to_csv(output_file, sep='\t', index=False)
                self.log_progress(f'分析完成，结果已保存到: {output_file}')
                
                self.statusBar().showMessage('分析完成') 


            else:
                self.hide_progress()
                QMessageBox.warning(self, '警告', '分析失败')
        except Exception as e:
            self.hide_progress()
            import traceback
            error_msg = f'分析过程中出错:\n{str(e)}\n\n完整错误追踪:\n{traceback.format_exc()}'
            QMessageBox.critical(self, '错误', error_msg)
            self.log_progress(f'错误: {error_msg}')
            print(f"Error details:\n{error_msg}")  # 打印详细错误信息到控制台

    def on_method_changed(self):
        """当分析方法改变时更新UI"""
        self.gsea_params_widget.setVisible(self.gsea_radio.isChecked())

def main():
    app = QApplication(sys.argv)
    window = EnrichmentApp()
    window.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()
