import os
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from scipy.stats import pearsonr

# 1. dir setup
p_dir = r"D:\ECNU\知识与考试\计算机\数据可视化\期末项目"
in_fp = os.path.join(p_dir, "ProcessedData", "uhi_matrix.parquet")
out_dir = os.path.join(p_dir, "Figures")
os.makedirs(out_dir, exist_ok=True)

# 2. load data & clean
df = pd.read_parquet(in_fp)
# 剔除那 8 个 ndvi 缺失的脏数据，防止 scipy 报错
df = df.dropna(subset=['ndvi'])

# style setup for high-quality plots
sns.set_theme(style="whitegrid", palette="muted")
plt.rcParams['font.sans-serif'] = ['SimHei'] # 允许图表中显示中文
plt.rcParams['axes.unicode_minus'] = False   # 正常显示负号

print("Start plotting...")

# ==========================================
# Chart 1: 多年夏季热岛强度演变趋势 (Time Series)
# ==========================================
# 只筛选夏季数据
sum_df = df[df['sea'] == 'Summer']
# 按年份求全城白天均值
trend = sum_df.groupby('yr')['uhii_d'].mean().reset_index()

fig1, ax1 = plt.subplots(figsize=(8, 5))
sns.lineplot(data=trend, x='yr', y='uhii_d', marker='o', linewidth=2.5, markersize=8, ax=ax1)
ax1.set_xticks([2022, 2023, 2024, 2025])
ax1.set_title("上海市夏季白天平均热岛强度演变 (2022-2025)", fontsize=14)
ax1.set_xlabel("年份 (Year)")
ax1.set_ylabel("平均热岛强度 (℃)")
fig1.savefig(os.path.join(out_dir, "1_Summer_UHI_Trend.png"), dpi=300, bbox_inches='tight')
print("Chart 1 saved.")

# ==========================================
# Chart 2: 城市公园的降温效应 (NDVI vs Temperature)
# ==========================================
# 选取 2025 年夏季进行截面分析，由于数据量大（上万个点），我们随机抽样 2000 个点画散点图防密集
df_25s = df[(df['yr'] == 2025) & (df['sea'] == 'Summer')].sample(n=2000, random_state=42)

# 计算皮尔逊相关系数和 P 值
corr, pval = pearsonr(df_25s['ndvi'], df_25s['lst_d'])

fig2, ax2 = plt.subplots(figsize=(8, 6))
# 绘制带有回归拟合线的散点图
sns.regplot(data=df_25s, x='ndvi', y='lst_d', 
            scatter_kws={'alpha':0.4, 's':15, 'color':'#2ca02c'}, 
            line_kws={'color':'red', 'linewidth':2}, ax=ax2)

ax2.set_title("植被指数(NDVI)与地表温度呈显著负相关", fontsize=14)
ax2.set_xlabel("植被指数 (NDVI)")
ax2.set_ylabel("白天地表温度 (℃)")
ax2.text(0.95, 0.95, f"Pearson r = {corr:.2f}\np-value < 0.001", 
         transform=ax2.transAxes, ha='right', va='top', 
         bbox=dict(boxstyle="round,pad=0.3", fc="white", ec="gray", alpha=0.8))

fig2.savefig(os.path.join(out_dir, "2_Park_Cooling_Effect.png"), dpi=300, bbox_inches='tight')
print("Chart 2 saved.")

# ==========================================
# Chart 3: 昼夜热岛效应对比 (Day vs Night Boxplot)
# ==========================================
# 将宽表转换为长表(melt)方便画箱线图
df_melt = pd.melt(sum_df, id_vars=['yr'], value_vars=['uhii_d', 'uhii_n'], 
                  var_name='Time', value_name='UHII')
df_melt['Time'] = df_melt['Time'].map({'uhii_d': '白天 (Day)', 'uhii_n': '夜间 (Night)'})

fig3, ax3 = plt.subplots(figsize=(8, 6))
sns.boxplot(data=df_melt, x='yr', y='UHII', hue='Time', fliersize=1, ax=ax3)
ax3.set_title("上海夏季昼夜热岛强度分布对比", fontsize=14)
ax3.set_xlabel("年份 (Year)")
ax3.set_ylabel("热岛强度 (℃)")
ax3.axhline(0, color='red', linestyle='--', linewidth=1, alpha=0.7) # 添加 0度基准线

fig3.savefig(os.path.join(out_dir, "3_Day_Night_UHI.png"), dpi=300, bbox_inches='tight')
print("Chart 3 saved.")

print("All static analysis complete! Check the 'Figures' folder.")