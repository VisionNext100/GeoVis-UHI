// ==========================================
// 上海 UHI 数据提取 —— 我们的目标是星辰大海！
// 特性：2022-2025；四季昼夜 + NDVI；中位数合成抗噪；1km网格对齐
// ==========================================

// 1. 安全获取区域边界 (使用市中心坐标点匹配行政边界，避免误差)
var pt = ee.Geometry.Point([121.4737, 31.2304]); // 上海市中心人民广场坐标
var roi = ee.FeatureCollection("FAO/GAUL/2015/level1")
    .filterBounds(pt);
Map.centerObject(roi, 10);
Map.addLayer(roi, { color: 'grey' }, 'Shanghai Boundary', false);

// 2. 导出建成区底图 (用于后续 3D 与空间统计)
var esa = ee.ImageCollection('ESA/WorldCover/v100').first();
var built1km = esa.eq(50).reduceNeighborhood({
    reducer: ee.Reducer.mean(),
    kernel: ee.Kernel.square(500, 'meters')
}).reproject({ crs: 'EPSG:4326', scale: 1000 }).rename('built_frac').clip(roi);

Export.image.toDrive({
    image: built1km, description: 'SH_Built_Frac_1km',
    folder: 'GEE_UHI_Project', scale: 1000, region: roi.geometry(), maxPixels: 1e9
});

// 3. 多年/多季节参数
var yrs = [2022, 2023, 2024, 2025];
var seas = [
    { name: 'Spring', flt: ee.Filter.calendarRange(3, 5, 'month') },
    { name: 'Summer', flt: ee.Filter.calendarRange(6, 8, 'month') },
    { name: 'Autumn', flt: ee.Filter.calendarRange(9, 11, 'month') },
    { name: 'Winter', flt: ee.Filter.or(ee.Filter.calendarRange(1, 2, 'month'), ee.Filter.calendarRange(12, 12, 'month')) }
];

// 4. 自动化构建导出任务队列
yrs.forEach(function (yr) {
    seas.forEach(function (sea) {
        var lst = ee.ImageCollection("MODIS/061/MOD11A2")
            .filterBounds(roi).filter(ee.Filter.calendarRange(yr, yr, 'year')).filter(sea.flt);
        var ndviColl = ee.ImageCollection("MODIS/061/MOD13A2")
            .filterBounds(roi).filter(ee.Filter.calendarRange(yr, yr, 'year')).filter(sea.flt);

        // 采用中位数合成 (Median) 提升抗噪性
        var lstMed = lst.median();
        var ndviMed = ndviColl.median();

        var d_C = lstMed.select('LST_Day_1km').multiply(0.02).subtract(273.15).rename('LST_Day_C');
        var n_C = lstMed.select('LST_Night_1km').multiply(0.02).subtract(273.15).rename('LST_Night_C');
        var ndvi = ndviMed.select('NDVI').multiply(0.0001).rename('NDVI');

        var finalImg = d_C.addBands(n_C).addBands(ndvi).clip(roi);

        Export.image.toDrive({
            image: finalImg,
            description: 'UHI_SH_' + yr + '_' + sea.name,
            folder: 'GEE_UHI_Project', scale: 1000, region: roi.geometry(), maxPixels: 1e9
        });
    });
});

print('任务队列构建完毕！请在 Tasks 面板依次点击 Run 提交。');