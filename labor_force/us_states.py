import json
import pandas as pd
import folium
with open("us_states.json") as f:
    geo_json_data = json.load(f)
labor_force = pd.read_csv("us_labor_force_2011.csv")
sattr = (
    '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> '
    'contributors, &copy; <a href="https://cartodb.com/attributions">CartoDB</a>'
)
m = folium.Map(
    location=[48, -100],
    zoom_start=4,
    tiles="https://mt.google.com/vt/lyrs=r&x={x}&y={y}&z={z}",
    # tiles=
    # "https://webrd04.is.autonavi.com/appmaptile?lang=zh_cn&size=1&scale=1&style=7&x={x}&y={y}&z={z}",
    attr=
    'Map Data &copy; <a href="https://earthengine.google.com/">Google Earth Engine</a>'
)

choropleth = folium.Choropleth(
    geo_data=geo_json_data,
    data=labor_force,
    columns=['State', "Civilian_labor_force"],
    key_on='id',
    fill_color='RdBu',
    use_jenks=True,
)
choropleth.add_to(m)
choropleth.color_scale.width = 800
m.save("us_states.html")  # 保存为html文件