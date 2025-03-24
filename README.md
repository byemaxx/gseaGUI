# GSEA GUI Toolset
# GSEA 图形界面工具集

A Python GUI toolset for Gene Set Enrichment Analysis (GSEA) and visualization. This toolset provides user-friendly graphical interfaces for:
这是一个用于基因集富集分析(GSEA)和可视化的Python图形界面工具集。该工具集提供了用户友好的图形界面，用于：

1. GSEA Result Visualization
   GSEA结果可视化
2. GMT File Generation
   GMT文件生成
3. Enrichment Analysis Tools
   富集分析工具


## Installation
## 安装

```bash
# Install from source
git clone https://github.com/byemaxx/gseagui.git
cd gseagui
pip install -e .

# Or install directly via pip
pip install gseagui
```

## Features
## 功能特点

### GSEA Result Visualization
### GSEA结果可视化

Visualize GSEA analysis results, supporting data import from pkl files and generating beautiful visualization charts.
可视化GSEA分析结果，支持从pkl文件导入数据并生成精美的可视化图表。

### GMT File Generator
### GMT文件生成器

Generate GMT format gene set files from annotation files, with various customization options.
从注释文件生成GMT格式的基因集文件，提供多种自定义选项。

### Enrichment Analysis Tools
### 富集分析工具

Provides core enrichment analysis functionality, supporting both hypergeometric enrichment analysis and GSEA analysis.
提供核心的富集分析功能，支持超几何富集分析和GSEA分析。

## Usage
## 使用方法

### Command Line Launch
### 命令行启动

```bash
# Launch main interface
gseagui

# Launch enrichment analysis tool
gseanrichment

# Launch GSEA visualization tool
gseaplotter

# Launch GMT generator
gmtgenerator
```

### Using in Python
### 在Python中使用

```python
import gseagui

# Launch enrichment analysis tool
from gseagui import EnrichmentApp
from PyQt5.QtWidgets import QApplication
import sys

app = QApplication(sys.argv)
window = EnrichmentApp()
window.show()
sys.exit(app.exec_())

# Or launch GSEA visualization tool
from gseagui import GSEAVisualizationGUI

app = QApplication(sys.argv)
window = GSEAVisualizationGUI()
window.show()
sys.exit(app.exec_())
```


## Project Structure
## 项目结构

The project uses modern `pyproject.toml` configuration instead of traditional `setup.py`:
项目使用现代的`pyproject.toml`配置替代传统的`setup.py`：

```
gseagui/
├── __init__.py        # Package initialization
├── enrichment_tools.py # Core enrichment functionality
├── gsea_runner.py     # Enrichment analysis GUI
├── gsea_res_ploter.py # GSEA result visualization GUI
├── gmt_generator.py   # GMT file generator
└── main.py           # Main launch interface
```

## Dependencies
## 依赖项

- pandas
- numpy
- matplotlib
- gseapy
- PyQt5

## License
## 许可证

This project is licensed under the BSD License. See the LICENSE file for details.
本项目采用BSD许可证。详细信息请参见LICENSE文件。
