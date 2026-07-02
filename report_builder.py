"""Build a factual UHI HTML report for one selected seasonal time slice."""

from __future__ import annotations

import html
import re
from datetime import datetime

import numpy as np
import pandas as pd
import plotly.io as pio
from plotly.offline.offline import get_plotlyjs

from config import SEASON_LABELS
from styles import apply_plotly_theme


SECTION_TITLES = {
    "spatial": "城市热岛空间格局",
    "profile": "城乡温度空间剖面",
    "park": "公园冷岛辐射效应",
    "ndvi": "NDVI 与地表温度关系",
    "history": "2022–2025 年际趋势",
}


def _fmt(value, digits=2, suffix=""):
    if value is None or pd.isna(value):
        return "暂无数据"
    return f"{value:.{digits}f}{suffix}"


def _period_label(time_of_day):
    return "白天" if "Day" in time_of_day or "白天" in time_of_day else "夜间"


def format_ai_message_html(message):
    """安全渲染 AI 文本中的换行与 Markdown 粗体。"""
    safe_message = html.escape(str(message))
    safe_message = re.sub(
        r"\*\*(.+?)\*\*",
        r"<strong>\1</strong>",
        safe_message,
    )
    return safe_message.replace("\n", "<br>")


def _figure_html(figure, div_id):
    if figure is None:
        return (
            '<div class="empty-state">'
            "当前筛选条件下数据不足，未生成该图表。"
            "</div>"
        )
    apply_plotly_theme(figure, height=430)
    return pio.to_html(
        figure,
        full_html=False,
        include_plotlyjs=False,
        config={"responsive": True, "displaylogo": False},
        div_id=div_id,
        default_height="430px",
    )


def _ai_html(ai_results, key):
    status, message = ai_results.get(
        key,
        ("missing", "本次未生成 AI 分析。"),
    )
    css_class = "ai-card" if status == "ok" else "ai-card ai-card-error"
    label = "DeepSeek 分析" if status == "ok" else "AI 状态说明"
    safe_message = format_ai_message_html(message)
    return (
        f'<div class="{css_class}">'
        f'<div class="ai-label"> {label}</div>'
        f"<p>{safe_message}</p></div>"
    )


def _history_metrics(full_data, season, uhii_col, lst_col):
    scoped = full_data[full_data["sea"] == season].copy()
    return (
        scoped.groupby("yr")
        .agg(
            mean_uhii=(uhii_col, "mean"),
            max_uhii=(uhii_col, "max"),
            mean_lst=(lst_col, "mean"),
            mean_ndvi=("ndvi", "mean"),
            sample_count=(uhii_col, "count"),
        )
        .reset_index()
        .sort_values("yr")
    )


def _history_table(history):
    rows = []
    for row in history.itertuples(index=False):
        rows.append(
            "<tr>"
            f"<td>{int(row.yr)}</td>"
            f"<td>{_fmt(row.mean_uhii, 2, ' ℃')}</td>"
            f"<td>{_fmt(row.max_uhii, 2, ' ℃')}</td>"
            f"<td>{_fmt(row.mean_lst, 1, ' ℃')}</td>"
            f"<td>{_fmt(row.mean_ndvi, 3)}</td>"
            f"<td>{int(row.sample_count):,}</td>"
            "</tr>"
        )
    if not rows:
        return '<tr><td colspan="6">暂无历史数据</td></tr>'
    return "".join(rows)


def build_seasonal_report(
    *,
    year,
    season,
    time_of_day,
    current_data,
    full_data,
    uhii_col,
    lst_col,
    ndvi_threshold,
    figures,
    ai_results,
    generated_at=None,
):
    """Return one HTML report for the selected year, season, and day/night slice."""
    generated_at = generated_at or datetime.now()
    period_label = _period_label(time_of_day)
    season_label = SEASON_LABELS.get(season, season)
    history = _history_metrics(full_data, season, uhii_col, lst_col)

    mean_uhii = current_data[uhii_col].mean()
    max_uhii = current_data[uhii_col].max()
    mean_lst = current_data[lst_col].mean()
    mean_ndvi = current_data["ndvi"].mean()
    strong_pct = (current_data[uhii_col] > 3).mean() * 100
    spatial_std = current_data[uhii_col].std()

    sample = current_data.dropna(subset=["ndvi", lst_col])
    sample = sample.sample(n=min(1500, len(sample)), random_state=42)
    corr = sample["ndvi"].corr(sample[lst_col]) if len(sample) >= 2 else np.nan
    slope = (
        np.polyfit(sample["ndvi"], sample[lst_col], 1)[0]
        if len(sample) >= 2 and sample["ndvi"].nunique() >= 2
        else np.nan
    )

    inner = current_data[current_data["dist_center"] <= 10][lst_col].mean()
    outer = current_data[current_data["dist_center"] >= 30][lst_col].mean()
    center_outer_delta = inner - outer

    park_stats = pd.DataFrame()
    if "buffer" in current_data and current_data["buffer"].notna().any():
        park_stats = (
            current_data.groupby("buffer", observed=False)[lst_col]
            .mean()
            .dropna()
        )
    park_delta = (
        park_stats.iloc[-1] - park_stats.iloc[0]
        if len(park_stats) >= 2
        else np.nan
    )

    selected_history = history[history["yr"] == year]
    selected_mean = (
        selected_history.iloc[0]["mean_uhii"]
        if not selected_history.empty
        else np.nan
    )
    ranked = history.sort_values("mean_uhii", ascending=False).reset_index(drop=True)
    rank_matches = ranked.index[ranked["yr"] == year].tolist()
    selected_rank = rank_matches[0] + 1 if rank_matches else None
    first_year = int(history.iloc[0]["yr"]) if not history.empty else None
    last_year = int(history.iloc[-1]["yr"]) if not history.empty else None
    history_change = (
        history.iloc[-1]["mean_uhii"] - history.iloc[0]["mean_uhii"]
        if len(history) >= 2
        else np.nan
    )

    previous = history[history["yr"] == year - 1]
    previous_delta = (
        selected_mean - previous.iloc[0]["mean_uhii"]
        if not previous.empty and not pd.isna(selected_mean)
        else np.nan
    )

    factual_summary = (
        f"{year} 年{season_label}（{period_label}）有效网格为 {len(current_data):,} 个，"
        f"平均热岛强度为 {_fmt(mean_uhii, 2, ' ℃')}，"
        f"平均地表温度为 {_fmt(mean_lst, 1, ' ℃')}。"
        f"在 {len(history)} 个可比较年份中，该年平均热岛强度排名"
        f" {selected_rank if selected_rank is not None else '暂无'}"
        f" / {len(history)}。"
    )

    plotly_js = get_plotlyjs()
    figure_blocks = {
        key: _figure_html(figures.get(key), f"report-{key}")
        for key in SECTION_TITLES
    }

    sections = f"""
    <section class="report-section" id="spatial">
      <div class="section-heading"><div><span>01 · SPATIAL PATTERN</span><h2>城市热岛空间格局</h2></div>
      <p>{year} 年当前切片的空间分布，不代表其他年份。</p></div>
      <div class="analysis-grid"><div class="chart-card">{figure_blocks["spatial"]}</div>
      <aside><div class="evidence-grid">
        <div><small>强热岛占比</small><b>{_fmt(strong_pct, 1, '%')}</b></div>
        <div><small>空间标准差</small><b>{_fmt(spatial_std, 2, ' ℃')}</b></div>
        <div><small>最高热岛强度</small><b>{_fmt(max_uhii, 2, ' ℃')}</b></div>
        <div><small>有效网格</small><b>{len(current_data):,}</b></div>
      </div>{_ai_html(ai_results, "spatial")}
      <details><summary>图表口径</summary><p>地图使用当前年份、当前季节和当前昼夜字段。热岛数据已嵌入报告；Carto 浅色底图需要联网加载，离线时仍可查看其他图表与统计信息。</p></details></aside></div>
    </section>

    <section class="report-section" id="profile">
      <div class="section-heading"><div><span>02 · URBAN–RURAL GRADIENT</span><h2>城乡温度空间剖面</h2></div>
      <p>当前季节切片从人民广场向外的温度梯度。</p></div>
      <div class="analysis-grid"><div class="chart-card">{figure_blocks["profile"]}</div>
      <aside><div class="evidence-grid">
        <div><small>0–10 km 均温</small><b>{_fmt(inner, 1, ' ℃')}</b></div>
        <div><small>30 km 外均温</small><b>{_fmt(outer, 1, ' ℃')}</b></div>
        <div><small>中心—外围温差</small><b>{_fmt(center_outer_delta, 1, ' ℃')}</b></div>
      </div>{_ai_html(ai_results, "profile")}
      <details><summary>分箱方法</summary><p>距离按 2 km 分箱，图中展示每个距离箱的平均地表温度。</p></details></aside></div>
    </section>

    <section class="report-section" id="park">
      <div class="section-heading"><div><span>03 · PARK COOLING</span><h2>公园冷岛辐射效应</h2></div>
      <p>当前季节切片不同公园距离环的温度分布。</p></div>
      <div class="analysis-grid"><div class="chart-card">{figure_blocks["park"]}</div>
      <aside><div class="evidence-grid">
        <div><small>远端－近端温差</small><b>{_fmt(park_delta, 2, ' ℃')}</b></div>
        <div><small>NDVI 季节阈值</small><b>{ndvi_threshold:.2f}</b></div>
        <div><small>有效缓冲环</small><b>{len(park_stats)}</b></div>
      </div>{_ai_html(ai_results, "park")}
      <details><summary>公园定义</summary><p>建成区占比低于 0.1 且 NDVI 高于当前季节阈值。</p></details></aside></div>
    </section>

    <section class="report-section" id="ndvi">
      <div class="section-heading"><div><span>04 · VEGETATION MECHANISM</span><h2>NDVI 与地表温度关系</h2></div>
      <p>当前季节切片植被覆盖与地表温度的统计关系。</p></div>
      <div class="analysis-grid"><div class="chart-card">{figure_blocks["ndvi"]}</div>
      <aside><div class="evidence-grid">
        <div><small>相关系数 r</small><b>{_fmt(corr, 3)}</b></div>
        <div><small>决定系数 R²</small><b>{_fmt(corr ** 2, 3)}</b></div>
        <div><small>回归斜率</small><b>{_fmt(slope, 2)}</b></div>
        <div><small>回归样本</small><b>{len(sample):,}</b></div>
      </div>{_ai_html(ai_results, "ndvi")}
      <details><summary>解释边界</summary><p>相关和回归描述统计关系，不单独证明因果关系。</p></details></aside></div>
    </section>

    <section class="report-section" id="history">
      <div class="section-heading"><div><span>05 · HISTORICAL CONTEXT</span><h2>2022–2025 同口径历史对照</h2></div>
      <p>仅此章节跨年份；季节与昼夜字段和当前报告保持一致。</p></div>
      <div class="analysis-grid"><div class="chart-card">{figure_blocks["history"]}</div>
      <aside><div class="evidence-grid">
        <div><small>{first_year or '起始年'}—{last_year or '结束年'}变化</small><b>{_fmt(history_change, 2, ' ℃')}</b></div>
        <div><small>{year} 年历史排名</small><b>{selected_rank or '暂无'} / {len(history)}</b></div>
        <div><small>相对上一年</small><b>{_fmt(previous_delta, 2, ' ℃')}</b></div>
      </div>{_ai_html(ai_results, "history")}
      <details><summary>历史比较口径</summary><p>逐年聚合同一季节、同一昼夜字段的全域平均热岛强度。四年序列仅作为近期对照。</p></details></aside></div>
      <div class="table-wrap"><table><thead><tr>
        <th>年份</th><th>平均热岛强度</th><th>最高热岛强度</th>
        <th>平均地表温度</th><th>平均 NDVI</th><th>网格数</th>
      </tr></thead><tbody>{_history_table(history)}</tbody></table></div>
    </section>
    """

    summary_cards = f"""
      <div class="summary-cards">
        <div><b>当前切片</b><p>{html.escape(factual_summary)}</p></div>
        <div><b>植被关系</b><p>NDVI–温度相关系数为 {_fmt(corr, 3)}，回归斜率为 {_fmt(slope, 2)}。</p></div>
        <div><b>公园距离环</b><p>最远与最近有效缓冲环的平均温差为 {_fmt(park_delta, 2, ' ℃')}。</p></div>
        <div><b>历史位置</b><p>{year} 年在同口径 {len(history)} 年比较中排名 {selected_rank or '暂无'}，相对上一年变化 {_fmt(previous_delta, 2, ' ℃')}。</p></div>
      </div>
    """

    return f"""<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<link rel="icon" href="data:,">
<title>{year} 年{season_label}（{period_label}）城市热岛效应专题报告</title>
<script>{plotly_js}</script>
<style>
:root{{--bg:#f2f5f9;--side:#eaf0f7;--panel:#ffffff;--soft:#eaf3ff;--line:#cfd9e6;--text:#253347;--muted:#5f6f82;--heading:#123b68;--blue:#1769c2;--blue-hover:#12579f;--cyan:#1769c2;--red:#b42318}}
*{{box-sizing:border-box}}html{{scroll-behavior:smooth}}body{{margin:0;background:var(--bg);color:var(--text);font:15px/1.7 "Microsoft YaHei",system-ui,sans-serif}}
.shell{{display:grid;grid-template-columns:250px minmax(0,1fr);max-width:1540px;margin:auto}}.side{{position:sticky;top:0;height:100vh;padding:28px 20px;border-right:1px solid var(--line);background:var(--side)}}
.brand{{font-size:18px;font-weight:800}}.brand b,.eyebrow,.section-heading span,.ai-label{{color:var(--cyan)}}.side small{{color:var(--muted)}}nav{{margin-top:24px}}nav a{{display:block;padding:9px 12px;color:#475467;text-decoration:none;border-radius:9px}}nav a:hover{{background:#eaf2ff;color:#175cd3}}
.main{{min-width:0;padding:28px 42px 80px}}.hero{{padding:22px 26px;border:1px solid var(--line);border-radius:16px;background:var(--panel);box-shadow:0 8px 24px rgba(38,66,94,.08)}}.hero h1{{font-size:32px;line-height:1.25;margin:7px 0;color:var(--heading)}}.hero p{{max-width:900px;margin:4px 0;color:var(--muted);font-size:15px}}
.pills{{display:flex;flex-wrap:wrap;gap:8px;margin-top:12px}}.pill{{padding:5px 11px;border:1px solid var(--line);border-radius:999px;background:var(--soft);color:#475467}}.print{{margin-top:14px;padding:9px 15px;border:0;border-radius:9px;background:var(--blue);color:#fff;font-weight:800;cursor:pointer;transition:.2s}}.print:hover{{background:var(--blue-hover);transform:translateY(-1px);box-shadow:0 4px 14px rgba(23,105,194,.24)}}
.tabs{{position:sticky;top:0;z-index:8;display:flex;gap:6px;margin:18px 0;padding:8px;border:1px solid var(--line);border-radius:12px;background:#ffffffee;box-shadow:0 4px 14px rgba(15,23,42,.05)}}.tabs button{{padding:9px 16px;border:0;border-radius:8px;background:transparent;color:var(--muted);cursor:pointer}}.tabs button.active{{background:#eaf2ff;color:#175cd3;font-weight:700}}.tab-panel:not(.active){{display:none!important}}
.report-section{{scroll-margin-top:90px;margin:30px 0}}.section-heading{{display:flex;justify-content:space-between;align-items:end;gap:20px;margin-bottom:14px}}.section-heading h2{{margin:3px 0 0;font-size:25px}}.section-heading p{{max-width:620px;margin:0;color:var(--muted)}}
.kpis{{display:grid;grid-template-columns:repeat(4,1fr);gap:12px;margin:18px 0}}.kpi,.summary-cards>div{{padding:18px;border:1px solid var(--line);border-radius:14px;background:var(--panel)}}.kpi small{{color:var(--muted)}}.kpi b{{display:block;font-size:27px;margin-top:6px}}
.analysis-grid{{display:grid;grid-template-columns:minmax(0,1.7fr) minmax(290px,.7fr);gap:14px}}.chart-card{{min-height:460px;padding:12px;border:1px solid var(--line);border-radius:15px;background:#fff;overflow:hidden}}aside{{display:flex;flex-direction:column;gap:12px}}
.evidence-grid{{display:grid;grid-template-columns:repeat(2,1fr);gap:8px}}.evidence-grid>div{{padding:12px;border:1px solid var(--line);border-radius:10px;background:#f7f9fc}}.evidence-grid small{{color:var(--muted)}}.evidence-grid b{{display:block;font-size:18px}}
.ai-card{{flex:1;padding:16px;border:1px solid #b7d2ee;border-left:4px solid var(--blue);border-radius:12px;background:var(--soft)}}.ai-card-error{{border-color:#fecdca;border-left-color:var(--red);background:#fff1f0}}.ai-card p{{margin-bottom:0}}details{{padding:10px 14px;border:1px solid var(--line);border-radius:10px;background:#f7f9fc;color:var(--muted)}}summary{{cursor:pointer;color:#344054;font-weight:700}}
.summary-cards{{display:grid;grid-template-columns:repeat(2,1fr);gap:12px}}.summary-cards b{{color:var(--cyan);font-size:17px}}.table-wrap{{margin-top:14px;overflow:auto;border:1px solid var(--line);border-radius:12px}}table{{width:100%;border-collapse:collapse;background:#fff}}th,td{{padding:11px 13px;border-bottom:1px solid var(--line);text-align:right;white-space:nowrap}}th:first-child,td:first-child{{text-align:left}}th{{color:#344054;background:#f2f4f7}}
.empty-state{{display:grid;place-items:center;min-height:410px;color:var(--muted)}}.method-card{{padding:20px;border:1px solid var(--line);border-radius:14px;background:var(--panel)}}footer{{margin-top:36px;padding-top:20px;border-top:1px solid var(--line);color:var(--muted)}}
@media(max-width:1050px){{.shell{{grid-template-columns:1fr}}.side{{display:none}}.main{{padding:20px}}.analysis-grid{{grid-template-columns:1fr}}}}
@media(max-width:650px){{.main{{padding:12px}}.hero{{padding:24px}}.hero h1{{font-size:29px}}.kpis,.summary-cards{{grid-template-columns:1fr}}.tabs{{overflow:auto}}.section-heading{{display:block}}}}
@media print{{.side,.tabs,.print{{display:none}}.shell{{display:block}}.main{{padding:0}}body{{background:#fff;color:#111}}.hero,.kpi,.chart-card,.ai-card,.method-card{{background:#fff;color:#111;break-inside:avoid}}}}
</style>
</head>
<body><div class="shell">
<aside class="side"><div class="brand">GeoVis <b>UHI</b></div><small>{year} 年{season_label}（{period_label}）专题报告</small>
<nav><a href="#overview">报告总览</a><a href="#spatial">01 空间格局</a><a href="#profile">02 城乡梯度</a><a href="#park">03 公园冷岛</a><a href="#ndvi">04 植被机制</a><a href="#history">05 历史对照</a></nav></aside>
<main class="main"><header class="hero" id="overview"><div class="eyebrow">SEASONAL UHI ANALYTICAL REPORT</div>
<h1>{year} 年{season_label}（{period_label}）城市热岛效应专题分析报告</h1>
<p>当前切片：{year} 年{season_label} · {period_label} · 上海市；历史章节对照 2022–2025 年同季节、同昼夜字段。</p>
<div class="pills"><span class="pill">{len(current_data):,} 个有效网格</span><span class="pill">历史对照：2022–2025</span></div>
<button class="print" onclick="window.print()">打印 / 另存 PDF</button></header>
<div class="tabs"><button class="active" data-tab="full">完整分析</button><button data-tab="summary">只看事实摘要</button><button data-tab="method">方法口径</button></div>
<div class="tab-panel active" id="full">
<section class="report-section"><div class="section-heading"><div><span>EXECUTIVE FACTS</span><h2>当前季节切片深度分析</h2></div><p>{html.escape(factual_summary)}</p></div>
<div class="kpis"><div class="kpi"><small>平均热岛强度</small><b>{_fmt(mean_uhii, 2, ' ℃')}</b></div><div class="kpi"><small>最高热岛强度</small><b>{_fmt(max_uhii, 2, ' ℃')}</b></div><div class="kpi"><small>平均地表温度</small><b>{_fmt(mean_lst, 1, ' ℃')}</b></div><div class="kpi"><small>平均 NDVI</small><b>{_fmt(mean_ndvi, 3)}</b></div></div></section>
{sections}</div>
<div class="tab-panel" id="summary"><section class="report-section"><div class="section-heading"><div><span>FACTUAL SUMMARY</span><h2>只看事实摘要</h2></div></div>{summary_cards}</section></div>
<div class="tab-panel" id="method"><section class="report-section" id="methods"><div class="section-heading"><div><span>METHODS & LIMITATIONS</span><h2>方法口径</h2></div></div>
<div class="method-card"><p><b>当前切片章节：</b>{year} 年{season_label}（{period_label}）。</p><p><b>历史章节：</b>2022–2025 同季节、同昼夜字段；不代表全年平均。</p><p><b>空间底图：</b>Carto 浅色底图需要联网加载，热岛数据与其他图表已嵌入 HTML。</p><p><b>水体处理：</b>仅使用 NDVI &gt; 0 的有效网格。</p><p><b>公园阈值：</b>建成区占比 &lt; 0.1，NDVI &gt; {ndvi_threshold:.2f}。</p><p><b>解释边界：</b>遥感地表温度不等于人体感知气温；相关关系不单独证明因果。</p></div></section></div>
<footer>生成时间：{generated_at.strftime('%Y-%m-%d %H:%M')} · 数据来源：MODIS 遥感影像 · GeoVis-UHI</footer>
</main></div>
<script>
document.querySelectorAll('.tabs button').forEach(button=>button.addEventListener('click',()=>{{document.querySelectorAll('.tabs button').forEach(x=>x.classList.remove('active'));document.querySelectorAll('.tab-panel').forEach(x=>x.classList.remove('active'));button.classList.add('active');document.getElementById(button.dataset.tab).classList.add('active')}}));
</script></body></html>"""
