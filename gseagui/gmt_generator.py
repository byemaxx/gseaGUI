import sys
import os
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                           QHBoxLayout, QPushButton, QFileDialog, QLabel, 
                           QComboBox, QTextEdit, QMessageBox, QProgressBar,
                           QCheckBox, QLineEdit, QGroupBox, QGridLayout,
                           QSpinBox)
import pandas as pd

try:
    from gseagui.qt_utils import fit_window_to_available_screen
except ImportError:
    from qt_utils import fit_window_to_available_screen

try:
    from gseagui.translations import TRANSLATIONS
except ImportError:
    from translations import TRANSLATIONS

class GMTGenerator(QMainWindow):
    def __init__(self, lang='en'):
        super().__init__()
        self.lang = lang
        self.trans = TRANSLATIONS["gmt"][self.lang]
        self.df_anno = None
        self.initUI()
        
    def initUI(self):
        self.setWindowTitle(self.trans["window_title"])
        fit_window_to_available_screen(self, 1000, 800)
        
        # 创建中央部件和主布局
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        
        # 文件选择区域
        file_group = QGroupBox(self.trans["input_group"])
        file_layout = QVBoxLayout()
        
        # 注释文件选择
        otf_layout = QHBoxLayout()
        self.otf_btn = QPushButton(self.trans["select_anno_btn"], self)
        self.otf_btn.clicked.connect(self.load_annotation_file)
        self.otf_label = QLabel(self.trans["no_file"], self)
        otf_layout.addWidget(self.otf_btn)
        otf_layout.addWidget(self.otf_label)
        file_layout.addLayout(otf_layout)
        
        # 列选择
        cols_layout = QGridLayout()
        self.id_col_label = QLabel(self.trans["id_col"], self)
        self.id_col_combo = QComboBox(self)
        self.anno_col_label = QLabel(self.trans["anno_col"], self)
        self.anno_col_combo = QComboBox(self)
        cols_layout.addWidget(self.id_col_label, 0, 0)
        cols_layout.addWidget(self.id_col_combo, 0, 1)
        cols_layout.addWidget(self.anno_col_label, 0, 2)
        cols_layout.addWidget(self.anno_col_combo, 0, 3)
        file_layout.addLayout(cols_layout)
        
        file_group.setLayout(file_layout)
        main_layout.addWidget(file_group)
        
        # 注释处理设置
        process_group = QGroupBox(self.trans["process_group"])
        process_layout = QGridLayout()
        
        # 分隔符设置
        self.split_check = QCheckBox(self.trans["enable_split"], self)
        self.split_check.setChecked(False)
        self.separator_label = QLabel(self.trans["separator"], self)
        self.separator_input = QLineEdit(self)
        self.separator_input.setText('|')
        process_layout.addWidget(self.split_check, 0, 0)
        process_layout.addWidget(self.separator_label, 0, 1)
        process_layout.addWidget(self.separator_input, 0, 2)
        
        # 过滤设置
        self.min_genes_label = QLabel(self.trans["min_genes"], self)
        self.min_genes_spin = QSpinBox(self)
        self.min_genes_spin.setValue(1)
        self.min_genes_spin.setRange(1, 10000)
        process_layout.addWidget(self.min_genes_label, 1, 0)
        process_layout.addWidget(self.min_genes_spin, 1, 1)
        
        # 无效值过滤
        self.invalid_values_label = QLabel(self.trans["invalid_values"], self)
        self.invalid_values_input = QLineEdit(self)
        self.invalid_values_input.setText('None,-,not_found,NA,nan')
        process_layout.addWidget(self.invalid_values_label, 2, 0)
        process_layout.addWidget(self.invalid_values_input, 2, 1, 1, 2)
        
        process_group.setLayout(process_layout)
        main_layout.addWidget(process_group)
        
        # 输出设置
        output_group = QGroupBox(self.trans["output_group"])
        output_layout = QGridLayout()
        
        self.output_dir_label = QLabel(self.trans["output_dir"], self)
        self.output_dir_input = QLineEdit(self)
        self.output_dir_input.setText('gmt_files')
        self.output_dir_btn = QPushButton(self.trans["select_btn"], self)
        self.output_dir_btn.clicked.connect(self.select_output_dir)
        output_layout.addWidget(self.output_dir_label, 0, 0)
        output_layout.addWidget(self.output_dir_input, 0, 1)
        output_layout.addWidget(self.output_dir_btn, 0, 2)
        
        output_group.setLayout(output_layout)
        main_layout.addWidget(output_group)
        
        # 进度条
        self.progress = QProgressBar(self)
        main_layout.addWidget(self.progress)
        
        # 日志区域
        log_group = QGroupBox(self.trans["log_group"])
        log_layout = QVBoxLayout()
        self.log_text = QTextEdit(self)
        self.log_text.setReadOnly(True)
        log_layout.addWidget(self.log_text)
        log_group.setLayout(log_layout)
        main_layout.addWidget(log_group)
        
        # 生成按钮
        self.generate_btn = QPushButton(self.trans["generate_btn"], self)
        self.generate_btn.clicked.connect(self.generate_gmt)
        main_layout.addWidget(self.generate_btn)
        
        # 初始化状态栏
        self.statusBar().showMessage(self.trans["status_ready"])
        
    def log(self, message):
        """添加日志消息"""
        self.log_text.append(message)
        self.log_text.verticalScrollBar().setValue(
            self.log_text.verticalScrollBar().maximum()
        )
        QApplication.processEvents()
        
    def load_annotation_file(self):
        """加载注释文件"""
        file_name, _ = QFileDialog.getOpenFileName(
            self, 
            self.trans["select_anno_btn"], 
            '', 
            'TSV files (*.tsv);;Text files (*.txt);;All Files (*)'
        )
        
        if file_name:
            try:
                self.log(self.trans["msg_loading"].format(file_name))
                self.df_anno = pd.read_csv(file_name, sep='\t')
                self.otf_label.setText(os.path.basename(file_name))
                
                # 更新列选择下拉框
                self.id_col_combo.clear()
                self.anno_col_combo.clear()
                self.id_col_combo.addItems(self.df_anno.columns)
                self.anno_col_combo.addItems(self.df_anno.columns)
                
                # 显示基本统计信息
                self.log(self.trans["msg_load_success"])
                self.log(f'  - 总行数: {len(self.df_anno)}')
                self.log(f'  - 总列数: {len(self.df_anno.columns)}')
                self.log(f'  - 列名: {", ".join(self.df_anno.columns)}')
                
            except Exception as e:
                QMessageBox.critical(self, self.trans["error"], self.trans["msg_load_fail"].format(str(e)))
                self.log(f'{self.trans["error"]}: {self.trans["msg_load_fail"].format(str(e))}')
    
    def select_output_dir(self):
        """选择输出目录"""
        dir_name = QFileDialog.getExistingDirectory(self, self.trans["output_dir"].replace(":", ""))
        if dir_name:
            self.output_dir_input.setText(dir_name)
            
    def generate_gmt(self):
        """生成GMT文件"""
        if self.df_anno is None:
            QMessageBox.warning(self, self.trans["warning"], self.trans["msg_select_anno_first"])
            return
            
        try:
            # 获取设置
            id_col = self.id_col_combo.currentText()
            anno_col = self.anno_col_combo.currentText()
            use_split = self.split_check.isChecked()
            separator = self.separator_input.text()
            min_genes = self.min_genes_spin.value()
            output_dir = self.output_dir_input.text()
            invalid_values = set(x.strip() for x in self.invalid_values_input.text().split(','))
            
            self.log(self.trans["msg_start_gen"])
            self.log(self.trans["msg_settings"])
            self.log(f'  - ID列: {id_col}')
            self.log(f'  - 注释列: {anno_col}')
            self.log(f'  - 启用分割: {use_split}')
            self.log(f'  - 分隔符: {separator}')
            self.log(f'  - 最小基因数: {min_genes}')
            self.log(f'  - 无效值: {invalid_values}')
            
            # 创建输出目录
            if not os.path.exists(output_dir):
                os.makedirs(output_dir)
                self.log(self.trans["msg_create_dir"].format(output_dir))
                
            # 生成gene sets
            gene_sets = {}
            total_rows = len(self.df_anno)
            valid_annotations = 0
            
            for index, row in self.df_anno.iterrows():
                gene_id = str(row[id_col])
                annotation = str(row[anno_col])
                
                if gene_id in invalid_values or pd.isnull(gene_id) or annotation in invalid_values or pd.isnull(annotation):
                    continue
                
                valid_annotations += 1
                pathways = [p.strip() for p in annotation.split(separator)] if use_split else [annotation.strip()]
                
                for pathway in pathways:
                    if pathway and pathway not in invalid_values:
                        if pathway not in gene_sets:
                            gene_sets[pathway] = set()
                        gene_sets[pathway].add(gene_id)
                
                if (index + 1) % 5000 == 0:
                    self.progress.setValue(int((index + 1) / total_rows * 100))
                    self.log(self.trans["msg_progress"].format(index + 1, total_rows))
            
            # 移除重复基因并应用最小基因数过滤
            filtered_gene_sets = {pathway: list(genes) for pathway, genes in gene_sets.items() if len(genes) >= min_genes}
            
            # 保存GMT文件
            output_file = os.path.join(output_dir, f'{anno_col}_geneset.gmt')
            with open(output_file, 'w', encoding='utf-8') as f:
                for pathway, genes in filtered_gene_sets.items():
                    f.write(f'{pathway}\tNA\t{"\t".join(genes)}\n')
            
            # 输出统计信息
            self.log(self.trans["msg_complete"])
            self.log(self.trans["msg_stats"])
            self.log(f'  - 总行数: {total_rows}')
            self.log(f'  - 有效注释数: {valid_annotations}')
            self.log(f'  - 原始通路数: {len(gene_sets)}')
            self.log(f'  - 过滤后通路数: {len(filtered_gene_sets)}')
            self.log(f'  - 已保存到: {output_file}')
            
            # 显示每个通路的基因数量分布
            gene_counts = [len(genes) for genes in filtered_gene_sets.values()]
            if gene_counts:
                self.log(self.trans["msg_gene_counts"])
                self.log(f'  - 最小值: {min(gene_counts)}')
                self.log(f'  - 最大值: {max(gene_counts)}')
                self.log(f'  - 平均值: {sum(gene_counts)/len(gene_counts):.2f}')
            
            self.progress.setValue(100)
            QMessageBox.information(self, self.trans["complete"], self.trans["msg_gen_complete"])
            
        except Exception as e:
            QMessageBox.critical(self, self.trans["error"], self.trans["msg_gen_error"].format(str(e)))
            self.log(f'{self.trans["error"]}: {self.trans["msg_gen_error"].format(str(e))}')
            self.progress.setValue(0)


def main():
    app = QApplication(sys.argv)
    window = GMTGenerator()
    window.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()