# GSEA GUI工具集

这是一个用于基因集富集分析(GSEA)和可视化的Python GUI工具包。该工具包提供了友好的图形界面，用于：
1. GSEA结果可视化
2. GMT文件生成
3. 富集分析工具

## 安装

```bash
# 从源码安装
git clone https://github.com/byemaxx/gseagui.git
cd gseagui
pip install -e .

# 或者直接通过pip安装
pip install gseagui
```

## 功能

### GSEA结果可视化

可视化GSEA分析结果，支持从pkl文件导入数据并生成美观的可视化图表。

### GMT文件生成器

从注释文件生成GMT格式的基因集文件，支持多种自定义选项。

### 富集分析工具

提供富集分析的核心功能，可用于执行超几何分布富集分析和GSEA分析。

## 使用方法

### 命令行启动

```bash
# 启动主界面
gseagui

# 启动富集分析工具
gseanrichment

# 启动GSEA可视化工具
gseaplotter

# 启动GMT生成器
gmtgenerator
```

### 在Python中使用

```python
import gseagui

# 启动富集分析工具
from gseagui import EnrichmentApp
from PyQt5.QtWidgets import QApplication
import sys

app = QApplication(sys.argv)
window = EnrichmentApp()
window.show()
sys.exit(app.exec_())

# 或者启动GSEA可视化工具
from gseagui import GSEAVisualizationGUI

app = QApplication(sys.argv)
window = GSEAVisualizationGUI()
window.show()
sys.exit(app.exec_())
```

## 项目结构

项目使用了现代化的`pyproject.toml`配置方案，不再依赖传统的`setup.py`：

```
gseagui/
├── __init__.py        # 包初始化文件
├── enrichment_tools.py # 富集分析核心功能
├── gsea_runner.py     # 富集分析GUI
├── gsea_res_ploter.py # GSEA结果可视化GUI
├── gmt_generator.py   # GMT文件生成器
└── main.py            # 主启动界面
```

## 依赖

- pandas
- numpy
- matplotlib
- gseapy
- PyQt5

## 许可

这个项目遵循BSD许可证。详见LICENSE文件。
