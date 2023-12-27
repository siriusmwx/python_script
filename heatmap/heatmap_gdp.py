import numpy as np
import pandas as pd
import folium
from folium.plugins import HeatMap

gdp_df = pd.read_excel("pop_gdp.xls")

num = 100

lat = np.array(gdp_df["LAT"][0:num])  # 获取维度之维度值
lon = np.array(gdp_df["LON"][0:num])  # 获取经度值
pop = np.array(gdp_df["POP"][0:num], dtype=float)  # 获取人口数，转化为numpy浮点型
gdp = np.array(gdp_df["GDP"][0:num], dtype=float)  # 获取GDP数，转化为numpy浮点型
gdp_average = np.array(gdp_df["GDP_Average"][0:num],
                       dtype=float)  # 获取人均GDP数，转化为numpy浮点型

data = [[lat[i], lon[i], gdp_average[i]]
        for i in range(num)]  #将数据制作成[lats,lons,weights]的形式

map_osm = folium.Map(
    location=[36, 105],
    # tiles="https://mt.google.com/vt/lyrs=r&x={x}&y={y}&z={z}",
    tiles=
    "https://wprd04.is.autonavi.com/appmaptile?lang=zh_cn&size=1&style=7&x={x}&y={y}&z={z}",
    zoom_start=5,
    attr="gaode")  #绘制Map，开始缩放程度是5倍
HeatMap(data).add_to(map_osm)  # 将热力图添加到前面建立的map里

map_osm.save("heat_map1.html")  # 保存为html文件