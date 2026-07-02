# -*- coding: utf-8 -*-
'''
AI 评估模块 — DeepSeek Chat API 调用 + 5 个图表数据摘要函数
'''

import json
import urllib.request
import urllib.error
import streamlit as st
import numpy as np

from config import (
    DEEPSEEK_API_KEY, DEEPSEEK_BASE_URL,
    DEEPSEEK_MODEL, DEEPSEEK_MAX_TOKENS, DEEPSEEK_TEMPERATURE,
)

# ============================================================
# Prompt 模板 — 5 个图表各一份
# ============================================================

PROMPT_TEMPLATES = {
    "heatmap": (
        "你是一位遥感与城市气候学专家。以下是上海市城市热岛效应的空间统计数据，"
        "请从以下角度给出简洁精炼的分析结论（150字以内）：\n"
        "1. 热岛核心区在哪里？空间聚集模式如何？\n"
        "2. 城乡温差梯度是否明显？\n"
        "3. 是否有异常高温或低温区域？\n"
        "请用中文回答，语气专业且适合课堂展示。"
    ),
    "profile": (
        "你是一位城市气候学专家。以下是以上海人民广场为中心向外辐射的城乡温度空间剖面数据。"
        "请分析（120字以内）：\n"
        "1. 温度随距离的递减趋势是否显著？\n"
        "2. 核心城区范围大约多少公里？\n"
        "3. 是否存在温度突变点？\n"
        "请用中文回答。"
    ),
    "park_buffer": (
        "你是一位城市生态学专家。以下是城市公园辐射缓冲区的降温效应统计数据。请分析（120字以内）：\n"
        "1. 公园的降温效应是否显著？\n"
        "2. 不同距离环的温差有多大？\n"
        "3. 降温效应在哪个距离开始衰减？\n"
        "请用中文回答。"
    ),
    "ndvi_scatter": (
        "你是一位植被遥感专家。以下是 NDVI 与地表温度的回归分析数据。请分析（120字以内）：\n"
        "1. 两者负相关有多强？\n"
        "2. 植被覆盖达到什么水平时降温效果最明显？\n"
        "3. 这对城市规划有何启示？\n"
        "请用中文回答。"
    ),
    "history_trend": (
        "你是一位气候数据分析师。以下是 2022-2025 年特定季节热岛强度逐年数据。"
        "请分析（120字以内）：\n"
        "1. 整体趋势是上升还是下降？\n"
        "2. 是否存在异常年份？\n"
        "3. 可能的原因是什么？\n"
        "请用中文回答。"
    ),
}

# ============================================================
# DeepSeek API 调用
# ============================================================

def call_deepseek(data_context, prompt):
    '''
    调用 DeepSeek Chat API（纯文本），发送数据统计 + 分析指令，返回分析文本。
    deepseek-chat 不支持多模态，所以只发文本统计数据。
    '''
    if not data_context:
        return ("error", "⚠️ 数据不足，无法进行分析。")
    if not DEEPSEEK_API_KEY:
        return (
            "error",
            "⚠️ 未配置 DEEPSEEK_API_KEY。请在项目根目录的 .env 文件中填写后重试。",
        )

    payload = {
        "model": DEEPSEEK_MODEL,
        "messages": [
            {
                "role": "system",
                "content": "你是一位遥感与城市气候学专家，擅长解读城市热岛效应数据。请用简洁准确的中文作答。",
            },
            {
                "role": "user",
                "content": f"{prompt}\n\n以下是数据摘要：\n{data_context}",
            }
        ],
        "max_tokens": DEEPSEEK_MAX_TOKENS,
        "temperature": DEEPSEEK_TEMPERATURE,
    }

    req = urllib.request.Request(
        DEEPSEEK_BASE_URL,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            result = json.loads(resp.read().decode("utf-8"))
            return ("ok", result["choices"][0]["message"]["content"].strip())
    except urllib.error.HTTPError as e:
        err_body = e.read().decode("utf-8", errors="replace")
        return ("error", f"API 请求失败 (HTTP {e.code}): {err_body[:200]}")
    except Exception as e:
        return ("error", f"网络或解析错误: {str(e)[:200]}")


@st.cache_data(show_spinner=False)
def cached_ai_analysis(cache_key, data_context, prompt):
    '''带 Streamlit 缓存的 AI 分析调用 — 同参数不重复请求'''
    return call_deepseek(data_context, prompt)


# ============================================================
# 5 个数据摘要生成器 — 不传图，传统计数字
# ============================================================

def summarize_heatmap(df_flt, uhii_col, lst_col, yr, sea):
    '''空间热力图统计摘要'''
    lines = [
        f"年份：{yr}，季节：{sea}",
        f"分析像素数：{len(df_flt)} 个（1km 网格）",
        f"全城平均热岛强度：{df_flt[uhii_col].mean():.2f} ℃",
        f"最高热岛强度：{df_flt[uhii_col].max():.2f} ℃",
        f"最低热岛强度：{df_flt[uhii_col].min():.2f} ℃",
        f"热岛强度标准差：{df_flt[uhii_col].std():.2f} ℃",
        f"平均地表温度：{df_flt[lst_col].mean():.1f} ℃",
        f"平均 NDVI：{df_flt['ndvi'].mean():.2f}",
    ]
    pct_strong = (df_flt[uhii_col] > 3).mean() * 100
    lines.append(f"强热岛（>3℃）占比：{pct_strong:.1f}%")
    return "\n".join(lines)


def summarize_profile(df_flt, lst_col):
    '''温度剖面统计摘要 — 输出距离分箱表'''
    prof = df_flt.groupby('dist_bin')[lst_col].agg(['mean', 'std', 'count']).reset_index()
    prof = prof[prof['dist_bin'] <= 50]
    lines = ["距离市中心(km) | 平均温度(℃) | 标准差 | 样本数"]
    for _, row in prof.iterrows():
        lines.append(
            f"{row['dist_bin']:6.0f}         | "
            f"{row['mean']:11.2f}     | "
            f"{row['std']:6.2f} | "
            f"{int(row['count']):6d}"
        )
    return "\n".join(lines)


def summarize_park_buffer(df_flt, lst_col):
    '''公园缓冲区统计摘要 — 输出各缓冲环统计'''
    if df_flt['buffer'].isnull().all() or df_flt['buffer'].nunique() < 2:
        return None
    stats = df_flt.groupby('buffer', observed=False)[lst_col].agg(
        ['mean', 'median', 'std', 'count']
    ).reset_index()
    lines = ["缓冲区          | 平均温度 | 中位数 | 标准差 | 样本数"]
    for _, row in stats.iterrows():
        lines.append(
            f"{row['buffer']:12s} | "
            f"{row['mean']:8.2f} | "
            f"{row['median']:6.2f} | "
            f"{row['std']:6.2f} | "
            f"{int(row['count']):6d}"
        )
    if len(stats) >= 2:
        inner = stats.iloc[0]['mean']
        outer = stats.iloc[-1]['mean']
        lines.append(f"\n最近缓冲区与最远缓冲区温差：{outer - inner:.2f} ℃")
    return "\n".join(lines)


def summarize_ndvi_scatter(df_flt, lst_col):
    '''NDVI-LST 回归统计摘要'''
    from config import SCATTER_SAMPLE_SIZE, RANDOM_SEED
    n = min(SCATTER_SAMPLE_SIZE, len(df_flt))
    s = df_flt.sample(n=n, random_state=RANDOM_SEED)
    slope, intercept = np.polyfit(s['ndvi'], s[lst_col], 1)
    corr = s['ndvi'].corr(s[lst_col])
    r2 = corr ** 2
    lines = [
        f"随机抽样样本数：{n}",
        f"NDVI 与地表温度相关系数 r：{corr:.4f}",
        f"决定系数 R²：{r2:.4f}",
        f"回归斜率：{slope:.2f} ℃/NDVI（NDVI 每增加 0.1，温度变化 {slope * 0.1:.2f} ℃）",
        f"回归截距：{intercept:.2f} ℃",
        f"NDVI 均值：{s['ndvi'].mean():.3f}，标准差：{s['ndvi'].std():.3f}",
        f"温度均值：{s[lst_col].mean():.2f} ℃，标准差：{s[lst_col].std():.2f} ℃",
    ]
    return "\n".join(lines)


def summarize_history_trend(df, sea, uhii_col):
    '''历史趋势统计摘要 — 输出逐年表'''
    hist = df[df['sea'] == sea].groupby('yr')[uhii_col].agg(['mean', 'std']).reset_index()
    lines = ["年份 | 平均热岛强度 | 标准差"]
    for _, row in hist.iterrows():
        lines.append(f"{int(row['yr'])}  | {row['mean']:13.2f} | {row['std']:6.2f}")
    if len(hist) >= 2:
        change = hist.iloc[-1]['mean'] - hist.iloc[0]['mean']
        lines.append(
            f"\n{int(hist.iloc[0]['yr'])}→{int(hist.iloc[-1]['yr'])} 变化：{change:+.2f} ℃"
        )
    return "\n".join(lines)
