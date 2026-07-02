import os
import glob
import numpy as np
import pandas as pd
import rasterio

# dir setup
p_dir = r"D:\ECNU\知识与考试\计算机\数据可视化\期末项目"
r_dir = os.path.join(p_dir, "RawData")
o_dir = os.path.join(p_dir, "ProcessedData")
os.makedirs(o_dir, exist_ok=True)

def process_uhi_data():
    # 1. read base grid (built fraction)
    bf_fp = os.path.join(r_dir, "SH_Built_Frac_1km.tif")
    
    with rasterio.open(bf_fp) as src:
        b_arr = src.read(1)
        h, w = b_arr.shape
        
        # calc center coords for each pixel
        cols, rows = np.meshgrid(np.arange(w), np.arange(h))
        xs, ys = rasterio.transform.xy(src.transform, rows, cols)
        
        lon = np.array(xs).flatten()
        lat = np.array(ys).flatten()
        b_frac = b_arr.flatten()

    res = []
    yrs = [2022, 2023, 2024, 2025]
    seas = ['Spring', 'Summer', 'Autumn', 'Winter']

    print("Start processing TIFs...")
    
    # 2. loop & align features
    for y in yrs:
        for s in seas:
            fp = os.path.join(r_dir, f"UHI_SH_{y}_{s}.tif")
            if not os.path.exists(fp):
                print(f"Miss: {y} {s}")
                continue
                
            with rasterio.open(fp) as src:
                # band 1: LST_Day, 2: LST_Night, 3: NDVI
                lst_d = src.read(1).flatten()
                lst_n = src.read(2).flatten()
                ndvi = src.read(3).flatten()
                
            # valid mask (remove nodata/water/ocean)
            # GEE empty regions are usually < -50 C or NaN
            valid = (lst_d > -50) & (~np.isnan(lst_d))
            
            # 3. calc UHI Intensity (UHII)
            # define rural: built fraction < 0.2 (20%)
            rural_mask = valid & (b_frac < 0.2)
            
            if rural_mask.sum() > 0:
                r_mean_d = lst_d[rural_mask].mean()
                r_mean_n = lst_n[rural_mask].mean()
            else:
                r_mean_d, r_mean_n = 0, 0
                
            # build tmp df
            tmp = pd.DataFrame({
                'lon': lon[valid],
                'lat': lat[valid],
                'b_frac': b_frac[valid],
                'yr': y,
                'sea': s,
                'lst_d': lst_d[valid],
                'lst_n': lst_n[valid],
                'ndvi': ndvi[valid]
            })
            
            # core metrics: UHI = LST - Rural_Mean
            tmp['uhii_d'] = tmp['lst_d'] - r_mean_d
            tmp['uhii_n'] = tmp['lst_n'] - r_mean_n
            
            res.append(tmp)
            print(f"Done: {y} {s}, Pixels: {len(tmp)}")

    # 4. concat & export
    df = pd.concat(res, ignore_index=True)
    
    # save as parquet (much faster I/O than csv for Streamlit)
    out_fp = os.path.join(o_dir, "uhi_matrix.parquet")
    df.to_parquet(out_fp, index=False)
    
    print(f"\nAll done! Total rows: {len(df)}")
    print(f"Saved to: {out_fp}")

if __name__ == "__main__":
    process_uhi_data()