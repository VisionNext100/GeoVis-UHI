# GeoVis-UHI

## 上海城市热岛效应多时相遥感可视化平台

本项目是《数据可视化》课程期末项目。项目基于 2022—2025 年上海市遥感数据，分析城市热岛效应的空间分布、城乡温度梯度、公园冷岛效应、植被降温关系和长期变化趋势，并通过 Streamlit 构建交互式可视化平台。

在线访问地址：

[https://geovis-uhi.streamlit.app/](https://geovis-uhi.streamlit.app/)

---

## 1. 项目主要功能

本项目包含以下功能：

1. **核心指标看板**  
   展示当前年份、季节和昼夜条件下的平均热岛强度、极端热岛点强温差、陆地平均地表温度和平均 NDVI。

2. **2D / 3D 热岛空间分布图**  
   使用 2D 热力图展示城市热岛空间格局，并使用 3D 温度山增强空间起伏感。

3. **城乡温度空间剖面**  
   以人民广场为中心，向外进行距离分箱，分析中心城区到郊区的温度变化。

4. **公园冷岛缓冲区分析**  
   根据绿地和公园距离划分缓冲区，比较不同距离范围内的地表温度差异。

5. **NDVI 与地表温度关系分析**  
   使用散点图和 OLS 回归分析植被覆盖与地表温度之间的关系。

6. **历史长周期热岛趋势**  
   对 2022—2025 年同季节数据进行聚合，观察热岛强度的长期变化。

7. **AI 智能分析与 HTML 报告生成**  
   调用 DeepSeek API，根据图表统计摘要自动生成中文分析结论，并可导出 HTML 专题报告。

---

## 2. 数据说明

项目中主要涉及两类数据：

### 2.1 原始 TIF 数据

原始数据来自 Google Earth Engine 导出的遥感栅格影像。

典型文件包括：

```text
RawData/
├── SH_Built_Frac_1km.tif
├── UHI_SH_2022_Spring.tif
├── UHI_SH_2022_Summer.tif
├── ...
└── UHI_SH_2025_Winter.tif
```

说明：

- `UHI_SH_YYYY_Season.tif`：某一年、某一季节的上海热岛遥感切片，通常包含白天地表温度、夜间地表温度和 NDVI 等信息。
- `SH_Built_Frac_1km.tif`：建成区密度栅格，用于区分城市建成区和乡村背景区。
- 这些 TIF 数据主要用于重新生成项目数据表。当前项目包已包含处理好的数据，因此普通运行不需要重新处理 TIF。

### 2.2 处理后的主数据表

```text
ProcessedData/uhi_matrix.parquet
```

这是 Streamlit 网页直接读取的核心数据表，已经将遥感栅格数据整理为可分析的空间网格样本，包含年份、季节、昼夜、经纬度、地表温度、NDVI、建成区比例、热岛强度等字段。

---

## 3. 数据处理流程

项目的数据流程如下：

```text
GEE 导出遥感 TIF
        ↓
1_data_process.py
读取 TIF、解析波段、展开坐标、计算热岛指标
        ↓
ProcessedData/uhi_matrix.parquet
项目主数据表
        ↓
4_streamlit_app.py
交互式可视化平台
```

另外还有两个辅助输出流程：

```text
uhi_matrix.parquet
        ↓
2_spatial_analysis.py
        ↓
Figures/*.png
用于论文、报告、PPT 和 README 的静态图
```

```text
uhi_matrix.parquet
        ↓
3_kepler_prep.py
        ↓
ProcessedData/kepler_data.csv
用于交互地图、时间轴地图或空间动画展示
```

---

## 4. 项目结构

```text
GeoVis-UHI-main/
├── ProcessedData/
│   └── uhi_matrix.parquet        # Streamlit 主程序使用的核心数据表
├── Figures/                      # 静态分析图
│   ├── 1_Summer_UHI_Trend.png
│   ├── 2_Park_Cooling_Effect.png
│   ├── 3_Day_Night_UHI.png
│   └── sanity_check.png
├── UHI_Data_Export.js            # GEE 数据导出脚本
├── 1_data_process.py             # 原始 TIF 数据处理脚本
├── 2_spatial_analysis.py         # 静态统计图生成脚本
├── 3_kepler_prep.py              # 交互地图数据生成脚本
├── 4_streamlit_app.py            # Streamlit 网页主入口
├── ai_evaluator.py               # AI 图表分析模块
├── ai_parallel.py                # AI 并发分析模块
├── report_builder.py             # HTML 报告生成模块
├── config.py                     # 项目配置
├── styles.py                     # 页面样式
├── requirements.txt              # Python 依赖
├── .env.example                  # API Key 配置模板
└── README.md                     # 项目说明文档
```

---

## 5. 快速复现

### 5.1 安装依赖

建议使用 Python 3.10 或以上版本。

在项目根目录打开终端，执行：

```shell
python -m pip install -r requirements.txt
```

### 5.2 配置 AI API Key（可选）

如果只想查看基础图表，可以跳过这一步，并在网页侧边栏关闭 AI 分析。

如果需要使用 AI 图表解读和 HTML 报告中的智能分析，需要复制 `.env.example`：

```shell
Copy-Item .env.example .env
```

然后打开 `.env`，填写自己的 DeepSeek API Key：

```text
DEEPSEEK_API_KEY=你的_API_Key
```

注意：`.env` 文件包含个人密钥，不要上传到公开仓库。

### 5.3 启动网页

执行：

```shell
python -m streamlit run 4_streamlit_app.py
```

启动后，浏览器会打开本地 Streamlit 页面。

---

## 6. 可选：重新生成数据和图表

如果只运行网页，不需要执行本节命令。

如果需要从原始 TIF 数据重新生成主数据表和图表，可按顺序执行：

```shell
python 1_data_process.py
python 2_spatial_analysis.py
python 3_kepler_prep.py
```

各脚本作用如下：

| 脚本                    | 作用                                                  |
| ----------------------- | ----------------------------------------------------- |
| `1_data_process.py`     | 读取原始 TIF，生成 `ProcessedData/uhi_matrix.parquet` |
| `2_spatial_analysis.py` | 生成 `Figures/` 中的静态分析图                        |
| `3_kepler_prep.py`      | 生成 `ProcessedData/kepler_data.csv`                  |
| `4_streamlit_app.py`    | 启动交互式可视化网页                                  |

---

## 7. AI 分析说明

AI 分析模块的作用是：根据图表背后的统计摘要，自动生成中文解释，而不是简单描述图片。

主要流程：

```text
当前筛选条件
    ↓
提取图表统计摘要
    ↓
选择对应 Prompt 模板
    ↓
调用 DeepSeek API
    ↓
返回中文分析结论
    ↓
显示在网页中，并写入 HTML 报告
```

项目中的 AI 分析覆盖：

- 空间热岛分布图
- 城乡温度空间剖面图
- 公园冷岛缓冲区图
- NDVI 与地表温度回归图
- 历史热岛强度趋势图

如果没有配置 API Key，可关闭 AI 分析，基础可视化功能仍可使用。

---

## 8. 运行注意事项

1. 当前项目包已经包含 `ProcessedData/uhi_matrix.parquet`，因此可以直接运行网页。
2. 如果要重新处理原始 TIF 数据，需要准备 `RawData/` 文件夹及对应 TIF 文件。
3. 地图底图、在线部署和 AI 分析需要联网。
4. `.env` 是本地密钥文件，不应提交到 GitHub。
5. 项目主入口是 `4_streamlit_app.py`。

---

## 9. 成果展示
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
    <img src="https://cdn.jsdelivr.net/gh/VisionNext100/Image-Hosting/images/GeoVis-UHI/城乡温度空间剖面图和城市公园辐射缓冲区降温效应（含AI分析）.png" width="800" alt="城乡温度空间剖面图和城市公园辐射缓冲区降温效应（含AI分析）">
    <br>
    <em>城乡温度空间剖面图和城市公园辐射缓冲区降温效应（含AI分析）, 2022 Summer, Night</em>
</div> 
<br>
<div align="center">
    <img src="https://cdn.jsdelivr.net/gh/VisionNext100/Image-Hosting/images/GeoVis-UHI/植被指数(NDVI)与地表温度定量演变和历史长周期热岛强度演变基准线（含AI分析）.png" width="800" alt="植被指数(NDVI)与地表温度定量演变和历史长周期热岛强度演变基准线（含AI分析）">
    <br>
    <em>植被指数(NDVI)与地表温度定量演变和历史长周期热岛强度演变基准线（含AI分析）, 2022 Summer, Night</em>
</div>

---

## 10. 项目总结

GeoVis-UHI 将遥感数据处理、空间可视化、机制分析、AI 图表解读和 HTML 报告生成连接起来，形成了一个完整的数据可视化项目流程。

项目最终回答了三个核心问题：

1. 上海城市热岛在哪里更明显？
2. 热岛强度如何随空间距离和城市生态因素变化？
3. 植被、公园和长期趋势如何帮助解释热岛变化？
