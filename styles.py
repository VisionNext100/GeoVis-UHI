# -*- coding: utf-8 -*-
"""Streamlit 与 Plotly 的雾蓝统一亮色主题。"""

import streamlit as st

from config import UI_COLORS


LIGHT_THEME_CSS = r"""
<style>
:root {
    --uhi-page: #F2F5F9;
    --uhi-side: #EAF0F7;
    --uhi-panel: #FFFFFF;
    --uhi-soft: #EAF3FF;
    --uhi-text: #253347;
    --uhi-muted: #5F6F82;
    --uhi-heading: #123B68;
    --uhi-accent: #1769C2;
    --uhi-accent-hover: #12579F;
    --uhi-line: #CFD9E6;
}
html, body, .stApp, [data-testid="stAppViewContainer"] {
    background-color: var(--uhi-page) !important;
    color: var(--uhi-text) !important;
}
[data-testid="stHeader"] {
    background: rgba(242, 245, 249, 0.96) !important;
    color: var(--uhi-text) !important;
    border-bottom: 1px solid var(--uhi-line);
}
[data-testid="stToolbar"], [data-testid="stDecoration"] {
    background: transparent !important;
    color: var(--uhi-text) !important;
}
.main .block-container {
    padding-top: 1.2rem;
    padding-bottom: 2rem;
    max-width: 95% !important;
}
h1 {
    color: var(--uhi-heading) !important;
    font-size: 2.4rem !important;
    font-weight: 700 !important;
    padding-bottom: 0.3rem;
    border-bottom: 2px solid var(--uhi-line);
    margin-bottom: 0.5rem;
}
h2, h3 { color: var(--uhi-accent) !important; font-weight: 650 !important; }

[data-testid="stMetric"] {
    background: var(--uhi-panel);
    border: 1px solid var(--uhi-line);
    border-radius: 14px;
    padding: 1.2rem 1rem;
    transition: transform 0.2s, box-shadow 0.2s;
    text-align: center;
    box-shadow: 0 4px 14px rgba(38, 66, 94, 0.08);
}
[data-testid="stMetric"]:hover {
    transform: translateY(-3px);
    box-shadow: 0 8px 24px rgba(23, 105, 194, 0.14);
}
[data-testid="stMetric"] label { color: var(--uhi-muted) !important; }
[data-testid="stMetric"] div[data-testid="stMetricValue"] {
    color: var(--uhi-accent) !important;
    font-size: 2rem !important;
    font-weight: 700 !important;
}
[data-testid="stSidebar"], [data-testid="stSidebarContent"] {
    background: var(--uhi-side) !important;
    color: var(--uhi-text) !important;
}
[data-testid="stSidebar"] { border-right: 1px solid var(--uhi-line); }

[data-testid="stSelectbox"] [data-baseweb="select"] > div {
    background: var(--uhi-panel) !important;
    color: var(--uhi-text) !important;
    border-color: var(--uhi-line) !important;
}
[data-testid="stSelectbox"] input,
[data-testid="stSelectbox"] svg {
    color: var(--uhi-text) !important;
    fill: var(--uhi-text) !important;
}
[data-baseweb="popover"] ul, [role="listbox"] {
    background: var(--uhi-panel) !important;
    color: var(--uhi-text) !important;
}
[role="option"] { color: var(--uhi-text) !important; }
[role="option"]:hover, [aria-selected="true"][role="option"] {
    background: var(--uhi-soft) !important;
}
[data-testid="stRadio"] label,
[data-testid="stRadio"] p,
[data-testid="stCheckbox"] label,
[data-testid="stCheckbox"] p,
[data-testid="stSelectbox"] label {
    color: var(--uhi-text) !important;
    opacity: 1 !important;
    font-weight: 500;
}

.stButton > button,
[data-testid="stDownloadButton"] button,
[data-testid="stBaseButton-secondary"] {
    background: var(--uhi-accent) !important;
    color: #FFFFFF !important;
    border: 1px solid var(--uhi-accent) !important;
    border-radius: 10px !important;
    padding: 0.5rem 1.2rem !important;
    font-weight: 650 !important;
    transition: all 0.2s;
}
.stButton > button:hover,
[data-testid="stDownloadButton"] button:hover,
[data-testid="stBaseButton-secondary"]:hover {
    background: var(--uhi-accent-hover) !important;
    color: #FFFFFF !important;
    border-color: var(--uhi-accent-hover) !important;
    transform: translateY(-1px);
    box-shadow: 0 4px 14px rgba(23, 105, 194, 0.24);
}
[data-testid="stDownloadButton"] button p,
[data-testid="stBaseButton-secondary"] p { color: #FFFFFF !important; }

.ai-card {
    background: var(--uhi-soft);
    border: 1px solid #B7D2EE;
    border-left: 4px solid var(--uhi-accent);
    border-radius: 10px;
    padding: 1rem 1.3rem;
    margin: 0.8rem 0 1rem 0;
    font-size: 0.92rem;
    line-height: 1.65;
    color: var(--uhi-text);
}
.ai-card::before {
    content: "🤖 AI 分析";
    display: block;
    font-size: 0.75rem;
    letter-spacing: 0.08em;
    color: var(--uhi-accent);
    margin-bottom: 0.5rem;
    font-weight: 650;
}
.ai-card-error {
    background: #FFF1F0;
    border: 1px solid #FECDCA;
    border-left: 4px solid #B42318;
    border-radius: 10px;
    padding: 0.8rem 1.2rem;
    margin: 0.8rem 0 1rem 0;
    color: #912018;
}
[data-testid="stAlert"] {
    border: 1px solid var(--uhi-line);
    background: rgba(255, 255, 255, 0.68);
    color: var(--uhi-text);
}
[data-testid="stPlotlyChart"], [data-testid="stPydeckChart"] {
    background: var(--uhi-panel);
    border-radius: 12px;
    overflow: hidden;
    border: 1px solid var(--uhi-line);
    box-shadow: 0 4px 14px rgba(38, 66, 94, 0.06);
}
hr { border-color: var(--uhi-line) !important; margin: 1.5rem 0 !important; }
@media (max-width: 768px) {
    h1 { font-size: 1.5rem !important; }
    [data-testid="stMetric"] div[data-testid="stMetricValue"] { font-size: 1.3rem !important; }
}
</style>
"""


def apply_plotly_theme(figure, *, height=None):
    """统一 Plotly 图表的雾蓝亮色背景、字体、坐标轴与悬浮提示。"""
    axis_style = {
        "gridcolor": UI_COLORS["grid"],
        "linecolor": UI_COLORS["line"],
        "tickfont": {"color": UI_COLORS["muted"]},
        "title": {"font": {"color": UI_COLORS["text"]}},
        "zerolinecolor": UI_COLORS["line"],
        "automargin": True,
    }
    layout = {
        "paper_bgcolor": UI_COLORS["panel"],
        "plot_bgcolor": UI_COLORS["panel"],
        "font": {
            "color": UI_COLORS["text"],
            "family": '"Microsoft YaHei", "Segoe UI", sans-serif',
        },
        "title": {"font": {"color": UI_COLORS["heading"]}},
        "hoverlabel": {
            "bgcolor": UI_COLORS["panel"],
            "bordercolor": UI_COLORS["line"],
            "font": {"color": UI_COLORS["text"], "size": 12},
        },
        "legend": {
            "font": {"color": UI_COLORS["text"]},
            "bgcolor": "rgba(255,255,255,0.8)",
        },
        "xaxis": axis_style,
        "yaxis": axis_style,
    }
    if height is not None:
        layout["height"] = height
    figure.update_layout(**layout)
    return figure


def inject_styles():
    """注入自定义样式到页面。"""
    st.markdown(LIGHT_THEME_CSS, unsafe_allow_html=True)
