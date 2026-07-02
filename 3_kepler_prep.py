import os
import pandas as pd

# 1. dir setup
p_dir = r"D:\ECNU\知识与考试\计算机\数据可视化\期末项目"
in_fp = os.path.join(p_dir, "ProcessedData", "uhi_matrix.parquet")
out_dir = os.path.join(p_dir, "ProcessedData")

print("Loading data for Kepler-gl preparation...")
df = pd.read_parquet(in_fp)

# 2. map season to standard date string for Kepler timeline asset
sea_map = {
    'Spring': '03-01',
    'Summer': '06-01',
    'Autumn': '09-01',
    'Winter': '12-01'
}

print("Generating continuous timelines...")
# vectorization mapping: combining year and mapped month/day
df['dt'] = df['yr'].astype(str) + '-' + df['sea'].map(sea_map) + ' 00:00:00'

# 3. data thinning & optimization
# remove redundant metrics to avoid browser lagging, keep core features only
keep_cols = ['lon', 'lat', 'dt', 'yr', 'sea', 'b_frac', 'uhii_d', 'uhii_n', 'ndvi']
df_kp = df[keep_cols].copy()

# 4. export light-weight files
# csv is highly recognized by Kepler.gl for automatic temporal parsing
out_csv = os.path.join(out_dir, "kepler_data.csv")
df_kp.to_csv(out_csv, index=False)

print(f"Kepler data prepared successfully!")
print(f"   - Shape: {df_kp.shape}")
print(f"   - Features kept: {keep_cols}")
print(f"   - Saved to: {out_csv}")