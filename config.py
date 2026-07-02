# -*- coding: utf-8 -*-
'''
上海市热岛效应数据探索平台 — 全局配置
集中管理：路径、常量、阈值、色阶、DeepSeek API 参数
'''

import os
from dotenv import load_dotenv

# ———————————————————————— 路径 ————————————————————————
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(CURRENT_DIR, ".env"))
DATA_DIR = os.path.join(CURRENT_DIR, "ProcessedData")
PARQUET_PATH = os.path.join(DATA_DIR, "uhi_matrix.parquet")

# ———————————————————————— 地理参数 ————————————————————————
CENTER_LON = 121.4737
CENTER_LAT = 31.2304
KM_PER_DEG_LON = 95.0
KM_PER_DEG_LAT = 111.0
PROFILE_MAX_RADIUS_KM = 50
PROFILE_BIN_SIZE_KM = 2

# ———————————————————————— 植被与公园阈值 ————————————————————————
NDVI_THRESHOLDS = {
    "Winter": 0.35,
    "Spring": 0.50,
    "Autumn": 0.50,
    "Summer": 0.60,
}
NDVI_FLOOR = 0.0
PARK_BUILDING_FRAC_MAX = 0.1
PARK_BUFFER_BINS = [-1, 0.5, 1, 2, 4, 100]
PARK_BUFFER_LABELS = [
    "0-0.5km (内环)",
    "0.5-1km (中环)",
    "1-2km (外环)",
    "2-4km (边缘)",
    ">4km (远离)",
]

# ———————————————————————— 图表常量 ————————————————————————
UHII_RANGE = {"uhii_d": (-4.0, 8.0), "uhii_n": (-2.0, 6.0)}
COLOR_SCALE = "jet"
PARK_PALETTE = ['#41b6c4', '#1d91c0', '#225ea8', '#253494', '#081d58']
SCATTER_GREEN = '#2ca02c'
LINE_RED = '#e74c3c'
TREND_BLUE = '#1f77b4'

CHART_HEIGHT_MAP = 500
CHART_HEIGHT_STANDARD = 400
SCATTER_SAMPLE_SIZE = 1500
RANDOM_SEED = 42

# ———————————————————————— 统一雾蓝亮色主题 ————————————————————————
UI_COLORS = {
    "page": "#F2F5F9",
    "sidebar": "#EAF0F7",
    "panel": "#FFFFFF",
    "soft": "#EAF3FF",
    "text": "#253347",
    "muted": "#5F6F82",
    "heading": "#123B68",
    "accent": "#1769C2",
    "accent_hover": "#12579F",
    "line": "#CFD9E6",
    "grid": "#DCE4EE",
    "error_bg": "#FFF1F0",
    "error": "#B42318",
}

# ———————————————————————— 3D 地图参数 ————————————————————————
ELEVATION_SCALE = 1500
COLUMN_RADIUS = 500
DEFAULT_ZOOM = 8.5
DEFAULT_PITCH = 45

# ———————————————————————— 筛选控件选项 ————————————————————————
YEARS = [2022, 2023, 2024, 2025]
SEASONS = ["Spring", "Summer", "Autumn", "Winter"]
SEASON_LABELS = {
    "Spring": "春季",
    "Summer": "夏季",
    "Autumn": "秋季",
    "Winter": "冬季",
}
TIME_OF_DAY = ["白天 (Day)", "夜间 (Night)"]

# ———————————————————————— DeepSeek API ————————————————————————
DEEPSEEK_API_KEY = os.environ.get("DEEPSEEK_API_KEY")
DEEPSEEK_BASE_URL = "https://api.deepseek.com/v1/chat/completions"
DEEPSEEK_MODEL = "deepseek-chat"
DEEPSEEK_MAX_TOKENS = 600
DEEPSEEK_TEMPERATURE = 0.7
