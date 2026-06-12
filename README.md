# GeoVis-UHI
## DataVis Final Project

### 一、项目简介
本项目为《数据可视化》期末课程最终交付成果。基于 Google Earth Engine ([https://code.earthengine.google.com](https://code.earthengine.google.com)) 平台，我提取了 2022-2025 年间 MODIS 高精度多时相卫星遥感影像，结合 ESA WorldCover 地表覆盖数据，深度量化并动态可视化了上海市城市热岛效应 (UHI) 的演变趋势。  
本项目旨在构建一个数据驱动的交互式探索平台，核心亮点包括：
- 全局核心指标看板：实时运算并提取当前时相切片下的核心气候特征，量化展示全城平均热岛强度、极端点强温差、陆地均温及整体植被覆盖度，提供直观的宏观数据基准与水体掩膜说明。
- 2D/3D 双引擎空间分布视窗：集成 Plotly 2D 精准像素热力图与基于 WebGL GPU 加速的 PyDeck 3D 动态“温度山”模型，用户可自由切换俯视学术量化视角与 360° 全景空间探索视角。
- 城乡温度空间剖面分析：以市中心（人民广场）为空间计算原点，向外辐射 50 公里进行等距网格分箱。后台实时绘制温度随距离递减的曲线，科学界定核心热岛影响圈的物理边界。  
- 公园冷岛辐射圈动态评估：引入符合植物物候学规律的 NDVI 自适应季节阈值算法。配合 cKDTree 高维空间索引技术，划分全域像素至最近绿地的距离环，科学论证城市公园的辐射降温效应。
- 植被降温机制定量验证：利用海量空间样本进行动态随机抽样，通过 OLS 线性回归散点图揭示 NDVI 与地表温度的负相关机制，直观呈现城市绿地对微气候的调节与消热能力。
- 历史长周期热岛演变基准线：跨年份聚合特定季节的全域热岛强度，动态计算并绘制 4 年周期的宏观气候变化基准走势折线，帮助用户直观回溯历史趋势。

### 二、项目结构 
需本地存放的已用“*”标明。
```
Shanghai-UHI-Dashboard/
│
├── *RawData/                  # GEE 导出的原始 TIF 栅格影像
│   ├── SH_Built_Frac_1km.tif  # 1公里分辨率建成区密度栅格，用于区分城市与乡村区域
│   ├── ……
│   └── UHI_SH_2025_Winter.tif # 各年份各季节上海地表温度及植被指数数据，用于热岛效应时空分析（共16份）
├── ProcessedData/             # Python 清洗后生成的轻量级数据集
│   ├── uhi_matrix.parquet     # 包含 12w+ 空间网格样本的核心数据表
│   └── *kepler_data.csv       # 专供 Kepler.gl 3D 渲染的时间序列底图
├── Figures/                   # Phase 3 生成的图表
│   ├── 1_Summer_UHI_Trend.png
│   ├── 2_Park_Cooling_Effect.png
│   └── 3_Day_Night_UHI.png
├── UHI_Data_Export.js         # [Phase 0] GEE 数据拉取脚本 (JavaScript)
├── 1_data_process.py          # [Phase 1] 空间栅格解析与特征对齐
├── 2_spatial_analysis.py      # [Phase 2] 统计分析与相关性图表绘制
├── 3_kepler_prep.py           # [Phase 3] 3D 动态时间轴数据提炼
├── 4_streamlit_app.py         # [Phase 4] Streamlit 交互式网页主程序
├── .gitignore
├── LICENSE              
└── README.md                
```

### 三、快速复现

1\. 为防止安装 keplergl 时路径长度超标，请在 Windows 中以管理员身份打开 PowerShell，然后输入以下命令：
``` shell
reg add "HKLM\SYSTEM\CurrentControlSet\Control\FileSystem" /v LongPathsEnabled /t REG_DWORD /d 1 /f
```
随后重启电脑。  
2\. 建议在 Anaconda Prompt 中完成下面的操作以配置环境：
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
3\. 在 Anaconda Prompt 中执行
```shell
streamlit run 4_streamlit_app.py
```
当然，由于我已经部署好了 Streamlit Cloud，你也可以直接访问 [https://geovis-uhi.streamlit.app](https://geovis-uhi.streamlit.app) 查看效果。作为 collaborator，你最好先按照上述步骤配置好环境，便于协作。

### 四、后续工作
1\. 项目微调：每次修改代码后，仅需在本地执行
```shell
streamlit run 4_streamlit_app.py
```
即可同步查看修改效果。在确认无误后（需与团队所有成员确认）再 push 至此仓库，Streamlit Cloud 会自动检测并更新应用。一旦仓库更新，[https://geovis-uhi.streamlit.app](https://geovis-uhi.streamlit.app) 页面即会同步发生变化。  
2\. 准备答辩：制作 slides、撰写报告。  

### 五、成品展示
<div align="center">
    <img src="https://cdn.jsdelivr.net/gh/VisionNext100/Image-Hosting/images/GeoVis-UHI/城市热岛空间分布特征2D平面热力图.png" width="800" alt="城市热岛空间分布特征2D平面热力图">
    <br>
    <em>城市热岛空间分布特征 2D 平面热力图, 2022 Summer, Day</em>
</div> 
<br>
<div align="center">
    <img src="https://cdn.jsdelivr.net/gh/VisionNext100/Image-Hosting/images/GeoVis-UHI/城市热岛空间分布特征3D立体温度山.png" width="800" alt="城市热岛空间分布特征3D立体温度山">
    <br>
    <em>城市热岛空间分布特征 3D 立体温度山, 2022 Summer, Day</em>
</div> 
<br>
<div align="center">
    <img src="https://cdn.jsdelivr.net/gh/VisionNext100/Image-Hosting/images/GeoVis-UHI/城乡温度空间剖面图和城市公园辐射缓冲区降温效应.png" width="800" alt="城乡温度空间剖面图和城市公园辐射缓冲区降温效应">
    <br>
    <em>城乡温度空间剖面图和城市公园辐射缓冲区降温效应, 2024 Autumn, Night</em>
</div> 
<br>
<div align="center">
    <img src="https://cdn.jsdelivr.net/gh/VisionNext100/Image-Hosting/images/GeoVis-UHI/植被指数（NDVI）与地表温度定量演变和历史长周期热岛强度演变基准线.png" width="800" alt="植被指数（NDVI）与地表温度定量演变和历史长周期热岛强度演变基准线">
    <br>
    <em>植被指数（NDVI）与地表温度定量演变和历史长周期热岛强度演变基准线, 2025 Spring, Night</em>
</div>