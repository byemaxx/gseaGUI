import pandas as pd
import gseapy as gp
from typing import Callable

class EnrichmentAnalyzer:
    def __init__(self):
        self.gene_sets = {}
        self.df_anno = None
        self.progress_callback = None
        
    def set_progress_callback(self, callback: Callable[[str], None]):
        """设置进度回调函数"""
        self.progress_callback = callback
        
    def log(self, message: str):
        """输出日志信息"""
        if self.progress_callback:
            self.progress_callback(message)
            
    def load_annotation(self, file_path):
        """加载注释文件"""
        self.log('正在加载注释文件...')
        self.df_anno = pd.read_csv(file_path, sep='\t')
        self.log(f'成功加载注释文件，包含{len(self.df_anno)}行数据')
        return list(self.df_anno.columns)

    from typing import Dict, Set
    
    def create_gene_sets(self, gene_col: str, anno_col: str, use_split: bool = True, separator: str = "|") -> bool:
        """创建基因集
        
        Args:
            gene_col: 基因列名
            anno_col: 注释列名
            use_split: 是否分割注释
            separator: 分隔符
        
        Returns:
            bool: 是否创建成功
        """
        if self.df_anno is None:
            self.log("错误：未加载注释文件")
            return False
        
        try:
            self.log('开始创建基因集...')
            self.log(f'使用列: {gene_col} -> {anno_col}')
            
            # 预处理：移除无效数据
            INVALID_VALUES = {'None', '-', 'not_found', 'nan'}
            valid_mask = ~(
                self.df_anno[gene_col].astype(str).isin(INVALID_VALUES) |
                self.df_anno[anno_col].astype(str).isin(INVALID_VALUES) |
                self.df_anno[gene_col].isna() |
                self.df_anno[anno_col].isna()
            )
            
            valid_data = self.df_anno[valid_mask]
            valid_entries = len(valid_data)
            
            # 使用字典推导式创建基因集
            gene_sets: Dict[str, Set[str]] = {}
            total_rows = len(valid_data)
            
            for idx, (gene, pathway) in enumerate(zip(valid_data[gene_col], valid_data[anno_col]), 1):
                if idx % 1000 == 0:
                    self.log(f'处理进度: {idx}/{total_rows} ({(idx/total_rows*100):.1f}%)')
                
                pathways = pathway.split(separator) if use_split else [pathway]
                
                for path in (p.strip() for p in pathways if p.strip()):
                    if path not in gene_sets:
                        gene_sets[path] = set()
                    gene_sets[path].add(str(gene))
    
            # 统计信息
            total_unique_genes = set().union(*gene_sets.values())
            
            self.log('\n基因集创建完成:')
            self.log(f'- 总条目数: {total_rows}')
            self.log(f'- 有效条目数: {valid_entries}')
            self.log(f'- 通路数量: {len(gene_sets)}')
            self.log(f'- 独特基因数: {len(total_unique_genes)}')
            
            # 转换set为list以保持与原代码兼容
            self.gene_sets = {k: list(v) for k, v in gene_sets.items()}
            return True
            
        except Exception as e:
            self.log(f"创建基因集时发生错误: {str(e)}")
            return False
        
    def load_gene_list_from_file(self, file_path, gene_col=None, rank_col=None):
        """从文件加载基因列表"""
        self.log('正在读取基因列表文件...')
        df = pd.read_csv(file_path, sep='\t')
        self.log(f'文件包含 {len(df)} 行数据')
        
        if gene_col is None:
            gene_col = df.columns[0]
            
        genes = df[gene_col].tolist()
        self.log(f'从 {gene_col} 列读取到 {len(genes)} 个基因')
        
        if rank_col is not None and rank_col in df.columns:
            ranks = df[rank_col].tolist()
            rank_dict = dict(zip(genes, ranks))
            self.log(f'从 {rank_col} 列读取到排序值')
            return genes, rank_dict
        
        return genes, None
        
    def parse_input_genes(self, text):
        """解析用户输入的基因列表"""
        self.log('正在解析输入的基因列表...')
        lines = text.strip().split('\n')
        genes = []
        ranks = []
        
        for line in lines:
            if not line.strip():
                continue
            parts = line.split('\t')
            genes.append(parts[0].strip())
            if len(parts) > 1:
                try:
                    ranks.append(float(parts[1].strip()))
                except ValueError:
                    continue
                    
        self.log(f'解析完成，检测到 {len(genes)} 个基因')
        if len(ranks) == len(genes):
            self.log('检测到排序值数据')
            rank_dict = dict(zip(genes, ranks))
            return genes, rank_dict
        return genes, None

    def do_hypergeometric(self, gene_list):
        """执行超几何分布富集分析"""
        if not self.gene_sets:
            return None
            
        try:
            self.log(f'开始超几何分布富集分析...')
            self.log(f'输入基因数: {len(gene_list)}')
            self.log(f'背景基因集数: {len(self.gene_sets)}')
            
            enr = gp.enrich(
                gene_list=gene_list,
                gene_sets=self.gene_sets,
                background=None,
                outdir=None,
                no_plot=True
            )
            
            self.log(f'分析完成，发现 {len(enr.results)} 个富集结果')
            return enr.results
        except Exception as e:
            self.log(f"富集分析失败: {str(e)}")
            return None
            
    def do_gsea(self, rank_dict):
        """执行GSEA分析"""
        if not self.gene_sets:
            return None
            
        try:
            self.log(f'开始GSEA分析...')
            self.log(f'输入基因数: {len(rank_dict)}')
            self.log(f'背景基因集数: {len(self.gene_sets)}')
            
            # 准备GSEA输入格式
            rnk = pd.Series(rank_dict)
            
            # 执行GSEA分析
            pre_res = gp.prerank(
                rnk=rnk,
                gene_sets=self.gene_sets,
                outdir=None,
                no_plot=True
            )
            
            self.log(f'分析完成，发现 {len(pre_res.res2d)} 个富集结果')
            return pre_res
        except Exception as e:
            self.log(f"GSEA分析失败: {str(e)}")
            return None

    def load_gmt(self, file_path):
        """加载GMT文件并转换为背景基因集"""
        self.log('正在加载GMT文件...')
        gene_sets = {}
        try:
            with open(file_path, 'r') as f:
                for line in f:
                    parts = line.strip().split('\t')
                    if len(parts) < 3:
                        continue
                    pathway = parts[0]
                    genes = parts[2:]
                    gene_sets[pathway] = set(genes)
            self.gene_sets = {k: list(v) for k, v in gene_sets.items()}
            self.log(f'成功加载GMT文件，包含{len(gene_sets)}个基因集')
        except Exception as e:
            self.log(f'加载GMT文件失败: {str(e)}')
