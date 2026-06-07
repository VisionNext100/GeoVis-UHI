import os
import numpy as np
import pandas as pd
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pydeck as pdk
from scipy.spatial import cKDTree

# 1. 页面基本配置
st.set_page_config(
    page_title="上海市热岛效应数据探索平台",
    page_icon="🌡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 2. 路径与数据加载（集成水体掩膜）
current_dir = os.path.dirname(os.path.abspath(__file__))
in_fp = os.path.join(current_dir, "ProcessedData", "uhi_matrix.parquet")

@st.cache_data
def load_clean_data():
    data = pd.read_parquet(in_fp).dropna(subset=['ndvi'])
    # 【水体掩膜】剔除 NDVI <= 0 的像素，确保分析纯净度
    data = data[data['ndvi'] > 0].copy()
    return data

df = load_clean_data()

# 3. 侧边栏交互控件
st.sidebar.title("🛠️ 控制面板")
st.sidebar.markdown("改变以下选项，网页将重新计算相关指标：")

yr_sel = st.sidebar.selectbox("选择年份 (Year)", [2022, 2023, 2024, 2025], index=0)
sea_sel = st.sidebar.radio("选择季节 (Season)", ["Spring", "Summer", "Autumn", "Winter"], index=1)
tod_sel = st.sidebar.radio("分析时段 (Time of Day)", ["白天 (Day)", "夜间 (Night)"], index=0)

# ==========================================
# 🌿 算法升级：自适应季节植被阈值 (物候修正)
# ==========================================
if sea_sel == 'Winter':
    ndvi_threshold = 0.35  
elif sea_sel in ['Spring', 'Autumn']:
    ndvi_threshold = 0.50  
else:
    ndvi_threshold = 0.60  

uhii_col = 'uhii_d' if tod_sel == "白天 (Day)" else 'uhii_n'
lst_col = 'lst_d' if tod_sel == "白天 (Day)" else 'lst_n'

# ==========================================
# ⚡ 后端核心：时空数据流实时计算引擎
# ==========================================
df_flt = df[(df['yr'] == yr_sel) & (df['sea'] == sea_sel)].copy()

# 空间坐标投影近似（1° lon ≈ 95km, 1° lat ≈ 111km）
df_flt['lon_km'] = df_flt['lon'] * 95
df_flt['lat_km'] = df_flt['lat'] * 111

# A. 城乡温度剖面梯度计算 
c_lon_km, c_lat_km = 121.4737 * 95, 31.2304 * 111
df_flt['dist_center'] = np.sqrt((df_flt['lon_km'] - c_lon_km)**2 + (df_flt['lat_km'] - c_lat_km)**2)
df_flt['dist_bin'] = (df_flt['dist_center'] // 2) * 2 
prof_df = df_flt.groupby('dist_bin')[lst_col].mean().reset_index()

# B. 城市公园辐射缓冲区计算
parks = df_flt[(df_flt['ndvi'] > ndvi_threshold) & (df_flt['b_frac'] < 0.1)]

if not parks.empty:
    p_coords = parks[['lon_km', 'lat_km']].values
    tree = cKDTree(p_coords)
    all_coords = df_flt[['lon_km', 'lat_km']].values
    dists, _ = tree.query(all_coords)
    df_flt['dist_park'] = dists
    
    bins = [-1, 0.5, 1, 2, 4, 100]
    lbls = ['0-0.5km (内环)', '0.5-1km (中环)', '1-2km (外环)', '2-4km (边缘)', '>4km (远离)']
    df_flt['buffer'] = pd.cut(df_flt['dist_park'], bins=bins, labels=lbls)
else:
    df_flt['buffer'] = None

# ==========================================
# 🎨 前端呈现：数据可视化组件渲染
# ==========================================
st.title("🌡️ 上海市热岛效应多时相遥感交互探索平台")
st.markdown(f"当前观测切片：**{yr_sel}年 {sea_sel} ({tod_sel})** | 水体已进行掩膜处理（NDVI > 0）")
st.markdown("---")

# KPI 指标看板
col1, col2, col3, col4 = st.columns(4)
col1.metric("全城平均热岛强度", f"{df_flt[uhii_col].mean():.2f} ℃")
col2.metric("极端热岛点强温差", f"{df_flt[uhii_col].max():.2f} ℃")
col3.metric("陆地平均地表温度", f"{df_flt[lst_col].mean():.1f} ℃")
col4.metric("全域平均绿化植被(NDVI)", f"{df_flt['ndvi'].mean():.2f}")
st.markdown("---")

# ==========================================
# 🗺️ 核心升级：2D/3D 双引擎地图无缝切换
# ==========================================
col_map_title, col_map_toggle = st.columns([1, 1])
with col_map_title:
    st.subheader("🗺️ 城市热岛空间分布特征 (1km 像素网格)")
with col_map_toggle:
    # 增加一个并排的开关，供用户自由切换地图引擎
    map_view = st.radio(
        "选择视图模式：", 
        ["2D 平面热力图", "3D 立体温度山"], 
        horizontal=True, 
        label_visibility="collapsed"
    )

if "2D" in map_view:
    # 渲染 2D Plotly 地图
    fig_map = px.scatter_mapbox(
        df_flt, lat="lat", lon="lon", color=uhii_col, 
        color_continuous_scale="jet", 
        range_color=[-2, 6] if uhii_col=='uhii_n' else [-4, 8],
        mapbox_style="carto-positron", zoom=9.2,
        center={"lat": 31.2304, "lon": 121.4737},
        labels={uhii_col: '热岛强度(℃)'}, height=500
    )
    fig_map.update_traces(marker=dict(size=6, opacity=0.8))
    fig_map.update_layout(margin={"r":0,"t":0,"l":0,"b":0})
    st.plotly_chart(fig_map, use_container_width=True)
else:
    # 渲染 3D PyDeck WebGL 地图
    # 颜色映射归一化处理
    min_val, max_val = (-2.0, 6.0) if uhii_col == 'uhii_n' else (-4.0, 8.0)
    df_flt['norm_uhi'] = ((df_flt[uhii_col] - min_val) / (max_val - min_val)).clip(0, 1)
    df_flt['color'] = df_flt['norm_uhi'].apply(lambda x: [int(255 * x), 50, int(255 * (1 - x)), 200])

    layer = pdk.Layer(
        "ColumnLayer",
        data=df_flt,
        get_position=['lon', 'lat'],
        get_elevation=uhii_col,
        elevation_scale=1500, # 拔高系数
        radius=500,           # 半径 500 米
        get_fill_color='color',
        pickable=True,
        auto_highlight=True,
    )
    view_state = pdk.ViewState(
        longitude=121.4737, latitude=31.2304,
        zoom=8.5, pitch=45, bearing=0
    )
    r = pdk.Deck(
        layers=[layer],
        initial_view_state=view_state,
        map_style="mapbox://styles/mapbox/dark-v10",
        tooltip={"text": "热岛强度: {uhii_d} ℃\n地表温度: {lst_d} ℃\nNDVI: {ndvi}"}
    )
    st.pydeck_chart(r, use_container_width=True)
    st.caption("**操作提示**：在地图上按住 **鼠标右键** 或 **Shift+左键** 并拖动，即可改变视角。")

st.markdown("---")

# ==========================================
# 第一排高级分析：空间剖面 & 辐射区
# ==========================================
col_l, col_r = st.columns(2)

with col_l:
    st.subheader("📈 城乡温度空间剖面图")
    fig_prof = px.line(
        prof_df, x='dist_bin', y=lst_col,
        labels={'dist_bin': '距离市中心距离 (km)', lst_col: '平均地表温度 (℃)'},
        title=f"{yr_sel}年 {sea_sel} 城乡温差梯度滑梯曲线"
    )
    fig_prof.update_traces(line=dict(color='#e74c3c', width=3), mode='lines+markers')
    fig_prof.add_vrect(x0=0, x1=10, fillcolor="red", opacity=0.1, layer="below", line_width=0, annotation_text="核心城区")
    st.plotly_chart(fig_prof, use_container_width=True)
    st.caption("注：计算以人民广场为地理原点，向外辐射 50km 进行等距空间分箱统计。")

with col_r:
    st.subheader("🌳 城市公园辐射缓冲区降温效应")
    if df_flt['buffer'].notnull().any():
        custom_palette = ['#41b6c4', '#1d91c0', '#225ea8', '#253494', '#081d58']
        fig_box = px.box(
            df_flt, x='buffer', y=lst_col,
            color='buffer', color_discrete_sequence=custom_palette,
            labels={'buffer': '到最近公园的距离', lst_col: '地表温度 (℃)'},
            title=f"{yr_sel}年 {sea_sel} 绿地辐射圈冷岛效应定量评估"
        )
        fig_box.update_layout(showlegend=False)
        st.plotly_chart(fig_box, use_container_width=True)
        st.caption(f"公园定义标准：建成区占比 < 0.1 且 NDVI > threshold。为符合植物物候规律，系统对 threshold 实行自适应调整（夏季 0.60，春秋 0.50，冬季 0.35）。")
    else:
        st.warning("⚠️ 当前时相下未检测到符合标准的大型公园绿地资产。")

st.markdown("---")

# ==========================================
# 📊 第二排高级分析：定量演变 & 历史基准线
# ==========================================
col_bl, col_br = st.columns(2)

with col_bl:
    st.subheader("📉 植被指数(NDVI)与地表温度定量演变")
    df_sample = df_flt.sample(n=min(1500, len(df_flt)), random_state=42)
    fig_scatter = px.scatter(
        df_sample, x="ndvi", y=lst_col, 
        trendline="ols", 
        trendline_color_override="red",
        labels={"ndvi": "植被指数 (NDVI)", lst_col: "地表温度 (℃)"},
        title=f"{yr_sel}年 {sea_sel} 城乡绿地消热效应散点拟合"
    )
    fig_scatter.update_traces(marker=dict(opacity=0.5, size=5, color='#2ca02c'))
    st.plotly_chart(fig_scatter, use_container_width=True)
    st.caption("注：红色直线为一元线性回归拟合线，直观呈现全城绿化度与地表温度的强负相关机制。")

with col_br:
    st.subheader("📊 历史长周期热岛强度演变基准线")
    history_trend = df[df['sea'] == sea_sel].groupby('yr')[uhii_col].mean().reset_index()
    fig_trend = go.Figure()
    fig_trend.add_trace(go.Scatter(
        x=history_trend['yr'], y=history_trend[uhii_col],
        mode='lines+markers', 
        line=dict(width=3, color='#1f77b4'), 
        marker=dict(size=8, symbol='circle')
    ))
    fig_trend.update_layout(
        xaxis=dict(tickmode='array', tickvals=[2022, 2023, 2024, 2025]),
        xaxis_title="年份 (Year)", 
        yaxis_title="平均热岛强度 (℃)",
        title=f"2022-2025 {sea_sel} 季节历史演变趋势",
        margin=dict(l=40, r=40, t=40, b=40)
    )
    st.plotly_chart(fig_trend, use_container_width=True)
    st.caption("注：展示特定季节跨越 4 年周期的宏观气候变化基准线，有助于捕捉异常气候事件。")

# 侧边栏项目简介
st.sidebar.markdown("---")
st.sidebar.subheader("📌 关于本项目")
st.sidebar.info(
    "**《数据可视化》期末课程项目**\n\n"
    "本项目基于 GEE 遥感数据，实现对上海市城市热岛效应的多时相动态量化分析。\n\n"
    "核心亮点：实时空间剖面提取、公园缓冲区量化、WebGL 3D 热岛山峰。\n\n"
    "技术栈：Python, GeoPandas, SciPy, Plotly, pydeck, Streamlit。"
)
st.sidebar.caption("团队成员：王业涵、郭炫麟、吴昱阳")