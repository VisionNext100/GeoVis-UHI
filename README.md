# GeoVis-UHI
## DataVis Final Project

### 一、项目简介
本项目为《数据可视化》期末课程最终交付成果。我们基于 Google Earth Engine (GEE) 平台提取了 2022-2025 年间 MODIS 高精度多时相卫星遥感影像，结合 ESA WorldCover 地表覆盖数据，深度量化并动态可视化了上海市城市热岛效应 (UHI) 的演变趋势。  
本项目旨在构建一个数据驱动的交互式探索平台，核心亮点包括：
- 多维特征融合： 统一 1km 空间网格，对齐昼夜地表温度 (LST)、植被指数 (NDVI) 与建成区占比数据。
- 严谨的量化分析： 提取“城乡温差梯度”，并通过 OLS 线性回归模型定量证实了城市绿地的降温效应（显著性 $p < 0.001$）。
- 全栈可视化应用： 从底层的学术统计图表生成，到前端包含全像素渲染热力图与 3D 流光时间轴的 Streamlit 仪表板。  

### 二、项目结构 
需本地存放的已用“*”标明。
```
Shanghai-UHI-Dashboard/
│
├── *RawData/                  # GEE 导出的原始 TIF 栅格影像
│   ├── SH_Built_Frac_1km.tif  # 1公里分辨率建成区密度栅格，用于区分城市与乡村区域
│   ├── ……
│   └── UHI_SH_2025_Winter.tif # 各年份各季节上海地表温度及植被指数数据，用于热岛效应时空分析（共16份）
├── *ProcessedData/            # Python 清洗后生成的轻量级数据集
│   ├── uhi_matrix.parquet     # 包含 12w+ 空间网格样本的核心数据表
│   └── kepler_data.csv        # 专供 Kepler.gl 3D 渲染的时间序列底图
├── Figures/                   # Phase 3 生成的图表
│   ├── 1_Summer_UHI_Trend.png
│   ├── 2_Park_Cooling_Effect.png
│   └── 3_Day_Night_UHI.png
├── UHI_Data_Export.js         # [Phase 1] GEE 数据拉取脚本 (JavaScript)
├── 1_data_process.py          # [Phase 2] 空间栅格解析与特征对齐
├── 2_spatial_analysis.py      # [Phase 3] 统计分析与相关性图表绘制
├── 3_kepler_prep.py           # [Phase 4] 3D 动态时间轴数据提炼
├── 4_streamlit_app.py         # [Phase 5] Streamlit 交互式网页主程序
├── .gitignore
├── LICENSE              
└── README.md                
```

### 三、快速复现

1. 为防止安装 keplergl 时路径长度超标，请在 Windows 中以管理员身份打开 PowerShell，然后输入以下命令，随后重启电脑：
``` shell
reg add "HKLM\SYSTEM\CurrentControlSet\Control\FileSystem" /v LongPathsEnabled /t REG_DWORD /d 1 /f
```
2. 建议在 Anaconda Prompt 中完成下面的操作以配置环境：
``` shell
# 创建环境并指定 Python 3.10，这是最兼容遥感库的版本
conda create -n uhi python=3.10 -y
# 激活环境
conda activate uhi
# 通过 conda-forge 安装地理空间库与 Jupyter
conda install -c conda-forge rasterio geopandas jupyter -y
# 安装其他需要的库（不要执行 pip install -r requirements.txt，那是部署 Streamlit Cloud 时用的）
pip install numpy pandas scipy matplotlib seaborn plotly folium keplergl streamlit statsmodels
```
