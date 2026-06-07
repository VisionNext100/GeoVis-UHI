import pandas as pd
import matplotlib.pyplot as plt

# 1. 读取刚生成的超级数据表
df = pd.read_parquet(r"ProcessedData\uhi_matrix.parquet")

print("========== 数据集基本信息 ==========")
print(df.info())

print("\n========== 核心指标数值分布 (查看是否有异常值) ==========")
# 只查看温度、NDVI和热岛强度的统计描述
print(df[['lst_d', 'lst_n', 'ndvi', 'uhii_d']].describe().round(2))

# 2. 空间可视化校验：画出 2025 年夏季的白天温度图
print("\n正在生成空间校验地图，请查看弹出的窗口...")
df_sub = df[(df['yr'] == 2025) & (df['sea'] == 'Summer')]

plt.figure(figsize=(10, 8))
# 使用散点图快速还原地图，c指定颜色映射列，cmap使用冷暖色调
plt.scatter(df_sub['lon'], df_sub['lat'], c=df_sub['lst_d'], cmap='coolwarm', s=8, alpha=0.9)
plt.colorbar(label='LST Day (Celsius)')
plt.title('Sanity Check: 2025 Summer Day LST - Shanghai')
plt.axis('equal') # 保持经纬度比例 1:1，防止地图被拉伸变形
plt.xlabel('Longitude')
plt.ylabel('Latitude')
plt.tight_layout()
plt.show()