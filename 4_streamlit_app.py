# -*- coding: utf-8 -*-
"""
上海市热岛效应多时相遥感交互探索平台 — Streamlit 主入口
数据可视化期末课程项目
"""

import os, time, hashlib
import numpy as np
import pandas as pd
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pydeck as pdk
from scipy.spatial import cKDTree

# ---- 模块导入 ----
from config import (
    YEARS, SEASONS, SEASON_LABELS, TIME_OF_DAY, NDVI_THRESHOLDS,
    UHII_RANGE, COLOR_SCALE, CHART_HEIGHT_MAP, CHART_HEIGHT_STANDARD,
    SCATTER_SAMPLE_SIZE, RANDOM_SEED, SCATTER_GREEN, LINE_RED,
    TREND_BLUE, PARK_PALETTE,
    ELEVATION_SCALE, COLUMN_RADIUS, DEFAULT_ZOOM, DEFAULT_PITCH,
    CENTER_LON, CENTER_LAT,
)
from ai_evaluator import (
    cached_ai_analysis, PROMPT_TEMPLATES,
    summarize_heatmap, summarize_profile, summarize_park_buffer,
    summarize_ndvi_scatter, summarize_history_trend,
)
from ai_parallel import run_parallel_ai_jobs
from report_builder import build_seasonal_report, format_ai_message_html
from styles import apply_plotly_theme, inject_styles

# ==========================================
# 页面基本配置
# ==========================================
st.set_page_config(
    page_title="上海市热岛效应数据探索平台",
    page_icon=" ",
    layout="wide",
    initial_sidebar_state="expanded",
)

inject_styles()

import plotly.io as pio
pio.templates.default = "plotly_white"

PRIMARY_MAP_RENDER_DELAY_SECONDS = 0.5

# ==========================================
# 数据加载（含水体掩膜 + 缓存过期检测）
# ==========================================
current_dir = os.path.dirname(os.path.abspath(__file__))
in_fp = os.path.join(current_dir, "ProcessedData", "uhi_matrix.parquet")

#  缓存过期检测：比较 parquet 文件修改时间
CACHE_FINGERPRINT_KEY = "parquet_mtime"
current_mtime = os.path.getmtime(in_fp) if os.path.exists(in_fp) else 0.0

if CACHE_FINGERPRINT_KEY in st.session_state:
    if st.session_state[CACHE_FINGERPRINT_KEY] != current_mtime:
        st.warning(
            " 检测到数据源已更新。建议点击下方按钮清除缓存后刷新页面。",
            icon=""
        )
        if st.button(" 清除缓存并刷新", type="primary"):
            st.cache_data.clear()
            st.session_state[CACHE_FINGERPRINT_KEY] = current_mtime
            st.rerun()
st.session_state[CACHE_FINGERPRINT_KEY] = current_mtime


@st.cache_data
def load_clean_data():
    data = pd.read_parquet(in_fp).dropna(subset=["ndvi"])
    data = data[data["ndvi"] > 0].copy()
    return data


df = load_clean_data()

# ==========================================
# 侧边栏 — 控制面板
# ==========================================
with st.sidebar:
    st.markdown("##  控制面板")
    st.markdown("调整参数后，图表与 AI 分析将实时更新：")
    st.markdown("---")

    yr_sel = st.selectbox(" 选择年份", YEARS, index=0)
    sea_sel = st.radio(
        " 选择季节",
        SEASONS,
        index=1,
        horizontal=True,
        format_func=lambda season: SEASON_LABELS[season],
    )
    tod_sel = st.radio(" 分析时段", TIME_OF_DAY, index=0, horizontal=True)

    st.markdown("---")
    enable_ai = st.checkbox(
        " 启用 AI 智能分析", value=True,
        help="关闭可节省 API Token，加快页面响应"
    )

    st.markdown("---")


    st.markdown("---")
    st.markdown("##  关于本项目")
    st.info(
        "**《数据可视化》期末课程项目**\n\n"
        "基于 MODIS 卫星遥感数据（2022-2025），对上海市城市热岛效应"
        "进行多时相动态量化分析。\n\n"
        "**核心功能**\n"
        "- 空间剖面提取\n"
        "- 公园缓冲区量化\n"
        "- 2D/3D 双引擎地图\n"
        "-  DeepSeek AI 解读\n\n"
        "**技术栈**\n"
        "Python · Plotly · PyDeck ·\n"
        "Streamlit · DeepSeek API"
    )
    st.caption("团队成员：王业涵、郭炫麟、吴昱阳")

# ==========================================
# 参数解析
# ==========================================
ndvi_threshold = NDVI_THRESHOLDS.get(sea_sel, 0.60)
season_label = SEASON_LABELS[sea_sel]
uhii_col = "uhii_d" if tod_sel == "白天 (Day)" else "uhii_n"
lst_col = "lst_d" if tod_sel == "白天 (Day)" else "lst_n"
report_period_label = "白天" if tod_sel == "白天 (Day)" else "夜间"
report_period_slug = "Day" if tod_sel == "白天 (Day)" else "Night"

# ==========================================
# 时空切片计算
# ==========================================
df_flt = df[(df["yr"] == yr_sel) & (df["sea"] == sea_sel)].copy()

df_flt["lon_km"] = df_flt["lon"] * 95
df_flt["lat_km"] = df_flt["lat"] * 111

c_lon_km, c_lat_km = CENTER_LON * 95, CENTER_LAT * 111
df_flt["dist_center"] = np.sqrt(
    (df_flt["lon_km"] - c_lon_km) ** 2
    + (df_flt["lat_km"] - c_lat_km) ** 2
)
df_flt["dist_bin"] = (df_flt["dist_center"] // 2) * 2
prof_df = df_flt.groupby("dist_bin")[lst_col].mean().reset_index()

parks = df_flt[
    (df_flt["ndvi"] > ndvi_threshold) & (df_flt["b_frac"] < 0.1)
]
if not parks.empty:
    p_coords = parks[["lon_km", "lat_km"]].values
    tree = cKDTree(p_coords)
    all_coords = df_flt[["lon_km", "lat_km"]].values
    dists, _ = tree.query(all_coords)
    df_flt["dist_park"] = dists
    bins = [-1, 0.5, 1, 2, 4, 100]
    lbls = [
        "0-0.5km (内环)", "0.5-1km (中环)",
        "1-2km (外环)", "2-4km (边缘)", ">4km (远离)",
    ]
    df_flt["buffer"] = pd.cut(df_flt["dist_park"], bins=bins, labels=lbls)
else:
    df_flt["buffer"] = None

# ==========================================
#  KPI 同比计算（与去年同季节对比）
# ==========================================
prev_yr = yr_sel - 1
df_prev = df[(df["yr"] == prev_yr) & (df["sea"] == sea_sel)]
has_prev = not df_prev.empty

if has_prev:
    delta_uhii = df_flt[uhii_col].mean() - df_prev[uhii_col].mean()
    delta_lst = df_flt[lst_col].mean() - df_prev[lst_col].mean()
    delta_ndvi = df_flt["ndvi"].mean() - df_prev["ndvi"].mean()
    delta_max = df_flt[uhii_col].max() - df_prev[uhii_col].max()


# ==========================================
# 辅助函数：注册 AI 分析任务并立即渲染占位卡片
# ==========================================
ai_jobs = []
ai_results = {}


def render_ai_message(placeholder, status, message):
    css_class = "ai-card" if status == "ok" else "ai-card-error"
    safe_message = format_ai_message_html(message)
    placeholder.markdown(
        f'<div class="{css_class}">{safe_message}</div>',
        unsafe_allow_html=True,
    )


def register_ai_job(report_key, cache_key, data_context, prompt_template):
    placeholder = st.empty()
    if not enable_ai:
        placeholder.caption(" AI 分析已关闭，可在侧边栏重新启用。")
        ai_results[report_key] = ("disabled", "AI 分析未启用。")
        return
    if not data_context:
        placeholder.caption(" 数据不足，跳过 AI 分析。")
        ai_results[report_key] = ("missing", "数据不足，未生成 AI 分析。")
        return

    render_ai_message(placeholder, "ok", " AI 分析中，请稍候…")
    ai_jobs.append({
        "report_key": report_key,
        "placeholder": placeholder,
        "cache_key": cache_key,
        "data_context": data_context,
        "prompt_template": prompt_template,
    })


def analyze_ai_job(job):
    return cached_ai_analysis(
        job["cache_key"],
        job["data_context"],
        job["prompt_template"],
    )


def apply_ai_result(job, result):
    status, message = result
    ai_results[job["report_key"]] = result
    render_ai_message(job["placeholder"], status, message)


# ==========================================
# 页面标题
# ==========================================
st.title(" 上海市热岛效应多时相遥感交互探索平台")
st.markdown(
    f"**当前观测切片：{yr_sel} 年{season_label}（{report_period_label}）**  |  "
    f"水体已掩膜（NDVI > 0）|  "
    + ("  |   AI 分析已启用" if enable_ai else "  |  ⏸ AI 分析已暂停")
)
st.markdown("---")

# ==========================================
#  KPI 指标看板（含同比 delta）
# ==========================================
col1, col2, col3, col4 = st.columns(4)
with col1:
    kwargs = {"label": " 全城平均热岛强度", "value": f"{df_flt[uhii_col].mean():.2f} ℃"}
    if has_prev:
        kwargs["delta"] = f"{delta_uhii:+.2f} ℃ vs {prev_yr}"
    st.metric(**kwargs)
with col2:
    kwargs = {"label": " 极端热岛点强温差", "value": f"{df_flt[uhii_col].max():.2f} ℃"}
    if has_prev:
        kwargs["delta"] = f"{delta_max:+.2f} ℃ vs {prev_yr}"
    st.metric(**kwargs)
with col3:
    kwargs = {"label": " 陆地平均地表温度", "value": f"{df_flt[lst_col].mean():.1f} ℃"}
    if has_prev:
        kwargs["delta"] = f"{delta_lst:+.1f} ℃ vs {prev_yr}"
    st.metric(**kwargs)
with col4:
    kwargs = {"label": " 全域平均植被 (NDVI)", "value": f"{df_flt['ndvi'].mean():.2f}"}
    if has_prev:
        kwargs["delta"] = f"{delta_ndvi:+.2f} vs {prev_yr}"
    st.metric(**kwargs)
st.markdown("---")

# ==========================================
#  图表 1：2D/3D 双引擎地图 + AI
# ==========================================
col_map_title, col_map_toggle = st.columns([1, 1])
with col_map_title:
    st.subheader(" 城市热岛空间分布特征 (1km 像素网格)")
with col_map_toggle:
    map_view = st.radio(
        "选择视图模式：",
        ["2D 平面热力图", "3D 立体温度山"],
        horizontal=True,
        label_visibility="collapsed",
    )

data_map = summarize_heatmap(df_flt, uhii_col, lst_col, yr_sel, sea_sel)
cache_map = f"map_{yr_sel}_{sea_sel}_{uhii_col}"

# 报告使用与网页一致的 Carto 浅色底图；地图瓦片打开时需要网络。
report_fig_spatial = px.scatter_map(
    df_flt,
    lat="lat",
    lon="lon",
    color=uhii_col,
    color_continuous_scale=COLOR_SCALE,
    range_color=list(UHII_RANGE[uhii_col]),
    map_style="carto-positron",
    zoom=9.2,
    center={"lat": CENTER_LAT, "lon": CENTER_LON},
    labels={
        uhii_col: "热岛强度 (℃)",
    },
    hover_data={
        "lon": ":.4f",
        "lat": ":.4f",
        lst_col: ":.1f",
        "ndvi": ":.3f",
    },
    custom_data=[lst_col, "ndvi"],
    title=(
        f"{yr_sel} 年{season_label} {report_period_label}"
        "城市热岛强度空间分布"
    ),
    height=500,
)
report_fig_spatial.update_traces(
    marker=dict(size=6, opacity=0.85),
    hovertemplate=(
        "<b>空间网格</b><br>"
        "经度：%{lon:.4f}<br>"
        "纬度：%{lat:.4f}<br>"
        "热岛强度：%{marker.color:.2f} ℃<br>"
        "地表温度：%{customdata[0]:.1f} ℃<br>"
        "NDVI：%{customdata[1]:.3f}"
        "<extra></extra>"
    ),
)
apply_plotly_theme(report_fig_spatial, height=500)
report_fig_spatial.update_layout(
    margin={"r": 0, "t": 45, "l": 0, "b": 0},
    paper_bgcolor="#ffffff",
)

if "2D" in map_view:
    min_val, max_val = UHII_RANGE[uhii_col]
    fig_map = px.scatter_map(
        df_flt,
        lat="lat", lon="lon",
        color=uhii_col,
        color_continuous_scale=COLOR_SCALE,
        range_color=[min_val, max_val],
        map_style="carto-positron",
        zoom=9.2,
        center={"lat": CENTER_LAT, "lon": CENTER_LON},
        labels={uhii_col: "热岛强度 (℃)"},
        custom_data=[lst_col, "ndvi"],
        height=CHART_HEIGHT_MAP,
    )
    fig_map.update_traces(
        marker=dict(size=6, opacity=0.85),
        hovertemplate=(
            "<b>空间网格</b><br>"
            "经度：%{lon:.4f}<br>"
            "纬度：%{lat:.4f}<br>"
            "热岛强度：%{marker.color:.2f} ℃<br>"
            "地表温度：%{customdata[0]:.1f} ℃<br>"
            "NDVI：%{customdata[1]:.3f}"
            "<extra></extra>"
        ),
        marker_colorbar=dict(
            title=dict(text="热岛强度 (℃)", font=dict(color="#344054", size=13)),
            tickfont=dict(color="#344054", size=11),
            thickness=18, len=0.7,
            outlinewidth=1, outlinecolor="#d0d5dd",
        ),
    )
    apply_plotly_theme(fig_map, height=CHART_HEIGHT_MAP)
    fig_map.update_layout(
        margin={"r": 0, "t": 0, "l": 0, "b": 0},
        paper_bgcolor="#ffffff",
        plot_bgcolor="#ffffff",
    )
    st.plotly_chart(
        fig_map,
        width="stretch",
        key="primary_uhi_map",
    )
    register_ai_job(
        "spatial",
        cache_map,
        data_map,
        PROMPT_TEMPLATES["heatmap"],
    )
else:
    df_flt_3d = df_flt.copy()
    min_val, max_val = UHII_RANGE[uhii_col]
    df_flt_3d["norm_uhi"] = (
        (df_flt_3d[uhii_col] - min_val) / (max_val - min_val)
    ).clip(0, 1)
    df_flt_3d["color"] = df_flt_3d["norm_uhi"].apply(
        lambda x: [int(255 * x), 50, int(255 * (1 - x)), 200]
    )
    df_flt_3d["uhii_display"] = df_flt_3d[uhii_col].map(
        lambda value: f"{value:.2f}"
    )
    df_flt_3d["lst_display"] = df_flt_3d[lst_col].map(
        lambda value: f"{value:.1f}"
    )
    df_flt_3d["ndvi_display"] = df_flt_3d["ndvi"].map(
        lambda value: f"{value:.3f}"
    )

    layer = pdk.Layer(
        "ColumnLayer",
        data=df_flt_3d,
        get_position=["lon", "lat"],
        get_elevation=uhii_col,
        elevation_scale=ELEVATION_SCALE,
        radius=COLUMN_RADIUS,
        get_fill_color="color",
        pickable=True,
        auto_highlight=True,
    )
    view_state = pdk.ViewState(
        longitude=CENTER_LON, latitude=CENTER_LAT,
        zoom=DEFAULT_ZOOM, pitch=DEFAULT_PITCH, bearing=0,
    )
    r = pdk.Deck(
        layers=[layer],
        initial_view_state=view_state,
        map_style=pdk.map_styles.CARTO_LIGHT,
        map_provider="carto",
        tooltip={
            "text": (
                "热岛强度: {uhii_display} ℃\n"
                "地表温度: {lst_display} ℃\n"
                "NDVI: {ndvi_display}"
            ),
            "style": {
                "backgroundColor": "#FFFFFF",
                "color": "#253347",
                "border": "1px solid #CFD9E6",
                "borderRadius": "8px",
                "boxShadow": "0 6px 18px rgba(38, 66, 94, 0.16)",
                "fontFamily": '"Microsoft YaHei", "Segoe UI", sans-serif',
            },
        },
    )
    st.pydeck_chart(
        r,
        width="stretch",
        key="primary_uhi_map_3d",
    )
    st.caption(" 按住鼠标右键或 Shift+左键拖动可旋转视角")
    register_ai_job(
        "spatial",
        cache_map,
        data_map,
        PROMPT_TEMPLATES["heatmap"],
    )

# 先将较重的 MapLibre/WebGL 主图发送给浏览器，再继续生成次级图表。
time.sleep(PRIMARY_MAP_RENDER_DELAY_SECONDS)

st.markdown("---")

# ==========================================
#  图表 2：城乡温度空间剖面 + AI
# ==========================================
col_l, col_r = st.columns(2)

with col_l:
    st.subheader(" 城乡温度空间剖面图")
    fig_prof = px.line(
        prof_df,
        x="dist_bin", y=lst_col,
        labels={"dist_bin": "距离市中心 (km)", lst_col: "平均地表温度 (℃)"},
        title=f"{yr_sel}年{season_label} 城乡温差梯度曲线",
    )
    fig_prof.update_traces(
        line=dict(color=LINE_RED, width=3), mode="lines+markers"
    )
    fig_prof.add_vrect(
        x0=0, x1=10, fillcolor="red", opacity=0.1,
        layer="below", line_width=0, annotation_text="核心城区",
    )
    apply_plotly_theme(fig_prof, height=CHART_HEIGHT_STANDARD)
    fig_prof.update_layout(
        height=CHART_HEIGHT_STANDARD,
        paper_bgcolor="#ffffff",
        plot_bgcolor="#ffffff",
    )
    st.plotly_chart(fig_prof, width="stretch")
    st.caption("以人民广场为地理原点，向外辐射 50km 进行等距空间分箱统计。")
    register_ai_job(
        "profile",
        f"prof_{yr_sel}_{sea_sel}_{lst_col}",
        summarize_profile(df_flt, lst_col),
        PROMPT_TEMPLATES["profile"],
    )

# ==========================================
#  图表 3：公园辐射缓冲区降温效应 + AI
# ==========================================
fig_box = None
with col_r:
    st.subheader(" 公园辐射缓冲区降温效应")
    if df_flt["buffer"].notnull().any() and df_flt["buffer"].nunique() >= 2:
        fig_box = px.box(
            df_flt,
            x="buffer", y=lst_col,
            color="buffer",
            color_discrete_sequence=PARK_PALETTE,
            labels={"buffer": "到最近公园的距离", lst_col: "地表温度 (℃)"},
            title=f"{yr_sel}年{season_label} 绿地辐射圈冷岛效应定量评估",
        )
        apply_plotly_theme(fig_box, height=CHART_HEIGHT_STANDARD)
        fig_box.update_layout(
            showlegend=False, height=CHART_HEIGHT_STANDARD,
            paper_bgcolor="#ffffff",
            plot_bgcolor="#ffffff",
        )
        st.plotly_chart(fig_box, width="stretch")
        st.caption(
            f"公园定义：建成区占比 < 0.1 且 NDVI > {ndvi_threshold}。"
            "系统对 NDVI 阈值实行自适应调整（夏季 0.60，春秋 0.50，冬季 0.35）。"
        )
        park_ctx = summarize_park_buffer(df_flt, lst_col)
        register_ai_job(
            "park",
            f"park_{yr_sel}_{sea_sel}_{lst_col}",
            park_ctx,
            PROMPT_TEMPLATES["park_buffer"],
        )
    else:
        st.warning(" 当前参数下绿地样本不足，无法生成公园降温分析。")

st.markdown("---")

# ==========================================
#  图表 4：NDVI 与地表温度定量演变 + AI
# ==========================================
col_bl, col_br = st.columns(2)

with col_bl:
    st.subheader(" NDVI 与地表温度定量关系")
    n_sample = min(SCATTER_SAMPLE_SIZE, len(df_flt))
    df_sample = df_flt.sample(n=n_sample, random_state=RANDOM_SEED)
    fig_scatter = px.scatter(
        df_sample,
        x="ndvi", y=lst_col,
        trendline="ols",
        trendline_color_override="red",
        labels={"ndvi": "植被指数 (NDVI)", lst_col: "地表温度 (℃)"},
        title=f"{yr_sel}年{season_label} 城乡绿地消热效应散点拟合",
    )
    fig_scatter.update_traces(
        marker=dict(opacity=0.5, size=5, color=SCATTER_GREEN)
    )
    apply_plotly_theme(fig_scatter, height=CHART_HEIGHT_STANDARD)
    fig_scatter.update_layout(
        height=CHART_HEIGHT_STANDARD,
        paper_bgcolor="#ffffff",
        plot_bgcolor="#ffffff",
    )
    st.plotly_chart(fig_scatter, width="stretch")
    st.caption(
        f"随机抽样 {n_sample} 个空间网格样本，OLS 线性回归拟合，"
        "展示全城绿化度与地表温度的负相关机制。"
    )
    register_ai_job(
        "ndvi",
        f"ndvi_{yr_sel}_{sea_sel}_{lst_col}",
        summarize_ndvi_scatter(df_flt, lst_col),
        PROMPT_TEMPLATES["ndvi_scatter"],
    )

# ==========================================
#  图表 5：历史长周期热岛强度演变 + AI
# ==========================================
with col_br:
    st.subheader(" 历史长周期热岛强度演变基准线")
    history_trend = (
        df[df["sea"] == sea_sel].groupby("yr")[uhii_col].mean().reset_index()
    )
    fig_trend = go.Figure()
    fig_trend.add_trace(
        go.Scatter(
            x=history_trend["yr"], y=history_trend[uhii_col],
            mode="lines+markers",
            line=dict(width=3, color=TREND_BLUE),
            marker=dict(size=8, symbol="circle"),
        )
    )
    fig_trend.update_layout(
        xaxis=dict(tickmode="array", tickvals=[2022, 2023, 2024, 2025]),
        xaxis_title="年份 (Year)",
        yaxis_title="平均热岛强度 (℃)",
        title=f"2022-2025 年{season_label}历史演变趋势",
        height=CHART_HEIGHT_STANDARD,
        paper_bgcolor="#ffffff",
        plot_bgcolor="#ffffff",
    )
    apply_plotly_theme(fig_trend, height=CHART_HEIGHT_STANDARD)
    st.plotly_chart(fig_trend, width="stretch")
    st.caption("跨年份聚合季节热岛强度均值，绘制 4 年宏观变化趋势。")
    register_ai_job(
        "history",
        f"hist_{sea_sel}_{uhii_col}",
        summarize_history_trend(df, sea_sel, uhii_col),
        PROMPT_TEMPLATES["history_trend"],
    )

st.markdown("---")
st.caption(
    " 数据来源：MODIS 卫星遥感影像 (2022-2025)  |  "
    " AI 分析由 DeepSeek Chat API 驱动  |  "
    " 数据可视化期末课程项目"
)

# 所有图表和 AI 占位卡片均已发送给前端，此时才并行请求 AI。
run_parallel_ai_jobs(
    ai_jobs,
    analyze=analyze_ai_job,
    on_result=apply_ai_result,
    max_workers=5,
)

# ==========================================
#  当前季节切片 HTML 专题报告
# ==========================================
report_html = build_seasonal_report(
    year=yr_sel,
    season=sea_sel,
    time_of_day=tod_sel,
    current_data=df_flt,
    full_data=df,
    uhii_col=uhii_col,
    lst_col=lst_col,
    ndvi_threshold=ndvi_threshold,
    figures={
        "spatial": report_fig_spatial,
        "profile": fig_prof,
        "park": fig_box,
        "ndvi": fig_scatter,
        "history": fig_trend,
    },
    ai_results=ai_results,
)

with st.sidebar:
    st.markdown("---")
    st.markdown(
        f"###  {yr_sel} 年{season_label}（{report_period_label}）专题报告"
    )
    st.download_button(
        label=(
            f" 生成并下载 {yr_sel} 年{season_label}"
            f"（{report_period_label}）HTML 专题报告"
        ),
        data=report_html,
        file_name=(
            f"UHI_Report_{yr_sel}_{sea_sel}_{report_period_slug}.html"
        ),
        mime="text/html",
        help=(
            f"生成 {yr_sel} 年{season_label}（{report_period_label}）专题分析，"
            "并附 2022–2025 同季节、同昼夜历史对照"
        ),
    )
    st.caption(
        "包含 5 张真实图表、真实 AI 结论、历史对照表和方法说明；"
        "空间底图打开时需要网络"
    )
