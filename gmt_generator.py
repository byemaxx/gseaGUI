import sys
import os
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                           QHBoxLayout, QPushButton, QFileDialog, QLabel, 
                           QComboBox, QTextEdit, QMessageBox, QProgressBar,
                           QCheckBox, QLineEdit, QGroupBox, QGridLayout,
                           QSpinBox)
import pandas as pd

class GMTGenerator(QMainWindow):
    def __init__(self):
        super().__init__()
        self.df_anno = None
        self.initUI()
        
    def initUI(self):
        self.setWindowTitle('GMT File Generator')
        self.setGeometry(100, 100, 1000, 800)
        
        # 创建中央部件和主布局
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        
        # 文件选择区域
        file_group = QGroupBox("输入设置")
        file_layout = QVBoxLayout()
        
        # 注释文件选择
        otf_layout = QHBoxLayout()
        self.otf_btn = QPushButton('选择注释文件', self)
        self.otf_btn.clicked.connect(self.load_annotation_file)
        self.otf_label = QLabel('未选择文件', self)
        otf_layout.addWidget(self.otf_btn)
        otf_layout.addWidget(self.otf_label)
        file_layout.addLayout(otf_layout)
        
        # 列选择
        cols_layout = QGridLayout()
        self.id_col_label = QLabel('ID列:', self)
        self.id_col_combo = QComboBox(self)
        self.anno_col_label = QLabel('注释列:', self)
        self.anno_col_combo = QComboBox(self)
        cols_layout.addWidget(self.id_col_label, 0, 0)
        cols_layout.addWidget(self.id_col_combo, 0, 1)
        cols_layout.addWidget(self.anno_col_label, 0, 2)
        cols_layout.addWidget(self.anno_col_combo, 0, 3)
        file_layout.addLayout(cols_layout)
        
        file_group.setLayout(file_layout)
        main_layout.addWidget(file_group)
        
        # 注释处理设置
        process_group = QGroupBox("注释处理设置")
        process_layout = QGridLayout()
        
        # 分隔符设置
        self.split_check = QCheckBox('启用注释分割', self)
        self.split_check.setChecked(False)
        self.separator_label = QLabel('分隔符:', self)
        self.separator_input = QLineEdit(self)
        self.separator_input.setText('|')
        process_layout.addWidget(self.split_check, 0, 0)
        process_layout.addWidget(self.separator_label, 0, 1)
        process_layout.addWidget(self.separator_input, 0, 2)
        
        # 过滤设置
        self.min_genes_label = QLabel('最小基因数:', self)
        self.min_genes_spin = QSpinBox(self)
        self.min_genes_spin.setValue(1)
        self.min_genes_spin.setRange(1, 10000)
        process_layout.addWidget(self.min_genes_label, 1, 0)
        process_layout.addWidget(self.min_genes_spin, 1, 1)
        
        # 无效值过滤
        self.invalid_values_label = QLabel('无效值 (用逗号分隔):', self)
        self.invalid_values_input = QLineEdit(self)
        self.invalid_values_input.setText('None,-,not_found,NA,nan')
        process_layout.addWidget(self.invalid_values_label, 2, 0)
        process_layout.addWidget(self.invalid_values_input, 2, 1, 1, 2)
        
        process_group.setLayout(process_layout)
        main_layout.addWidget(process_group)
        
        # 输出设置
        output_group = QGroupBox("输出设置")
        output_layout = QGridLayout()
        
        self.output_dir_label = QLabel('输出目录:', self)
        self.output_dir_input = QLineEdit(self)
        self.output_dir_input.setText('gmt_files')
        self.output_dir_btn = QPushButton('选择...', self)
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
        log_group = QGroupBox("处理日志")
        log_layout = QVBoxLayout()
        self.log_text = QTextEdit(self)
        self.log_text.setReadOnly(True)
        log_layout.addWidget(self.log_text)
        log_group.setLayout(log_layout)
        main_layout.addWidget(log_group)
        
        # 生成按钮
        self.generate_btn = QPushButton('生成GMT文件', self)
        self.generate_btn.clicked.connect(self.generate_gmt)
        main_layout.addWidget(self.generate_btn)
        
        # 初始化状态栏
        self.statusBar().showMessage('就绪')
        
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
            '选择注释文件', 
            '', 
            'TSV files (*.tsv);;Text files (*.txt);;All Files (*)'
        )
        
        if file_name:
            try:
                self.log(f'正在加载注释文件: {file_name}...')
                self.df_anno = pd.read_csv(file_name, sep='\t')
                self.otf_label.setText(os.path.basename(file_name))
                
                # 更新列选择下拉框
                self.id_col_combo.clear()
                self.anno_col_combo.clear()
                self.id_col_combo.addItems(self.df_anno.columns)
                self.anno_col_combo.addItems(self.df_anno.columns)
                
                # 显示基本统计信息
                self.log('成功加载注释文件:')
                self.log(f'  - 总行数: {len(self.df_anno)}')
                self.log(f'  - 总列数: {len(self.df_anno.columns)}')
                self.log(f'  - 列名: {", ".join(self.df_anno.columns)}')
                
            except Exception as e:
                QMessageBox.critical(self, '错误', f'无法加载文件: {str(e)}')
                self.log(f'错误: 加载注释文件失败 - {str(e)}')
    
    def select_output_dir(self):
        """选择输出目录"""
        dir_name = QFileDialog.getExistingDirectory(self, '选择输出目录')
        if dir_name:
            self.output_dir_input.setText(dir_name)
            
    def generate_gmt(self):
        """生成GMT文件"""
        if self.df_anno is None:
            QMessageBox.warning(self, '警告', '请先加载注释文件')
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
            
            self.log('\n开始生成GMT文件...')
            self.log(f'使用设置:')
            self.log(f'  - ID列: {id_col}')
            self.log(f'  - 注释列: {anno_col}')
            self.log(f'  - 启用分割: {use_split}')
            self.log(f'  - 分隔符: {separator}')
            self.log(f'  - 最小基因数: {min_genes}')
            self.log(f'  - 无效值: {invalid_values}')
            
            # 创建输出目录
            if not os.path.exists(output_dir):
                os.makedirs(output_dir)
                self.log(f'创建输出目录: {output_dir}')
                
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
                    self.log(f'处理进度: {index + 1}/{total_rows}')
            
            # 移除重复基因并应用最小基因数过滤
            filtered_gene_sets = {pathway: list(genes) for pathway, genes in gene_sets.items() if len(genes) >= min_genes}
            
            # 保存GMT文件
            output_file = os.path.join(output_dir, f'{anno_col}_geneset.gmt')
            with open(output_file, 'w', encoding='utf-8') as f:
                for pathway, genes in filtered_gene_sets.items():
                    f.write(f'{pathway}\tNA\t{"\t".join(genes)}\n')
            
            # 输出统计信息
            self.log('\n处理完成!')
            self.log(f'统计信息:')
            self.log(f'  - 总行数: {total_rows}')
            self.log(f'  - 有效注释数: {valid_annotations}')
            self.log(f'  - 原始通路数: {len(gene_sets)}')
            self.log(f'  - 过滤后通路数: {len(filtered_gene_sets)}')
            self.log(f'  - 已保存到: {output_file}')
            
            # 显示每个通路的基因数量分布
            gene_counts = [len(genes) for genes in filtered_gene_sets.values()]
            if gene_counts:
                self.log('\n通路基因数量统计:')
                self.log(f'  - 最小值: {min(gene_counts)}')
                self.log(f'  - 最大值: {max(gene_counts)}')
                self.log(f'  - 平均值: {sum(gene_counts)/len(gene_counts):.2f}')
            
            self.progress.setValue(100)
            QMessageBox.information(self, '完成', 'GMT文件生成完成！')
            
        except Exception as e:
            QMessageBox.critical(self, '错误', f'生成过程中出错: {str(e)}')
            self.log(f'错误: 生成失败 - {str(e)}')
            self.progress.setValue(0)


def main():
    app = QApplication(sys.argv)
    window = GMTGenerator()
    window.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()