import json
import pandas as pd
import folium

datas = {}
with open("china_state.json", encoding="utf-8") as f:
    geo_json_data = json.load(f)
# datas["type"] = geo_json_data["type"]
# datas["features"] = []
# for data in geo_json_data["features"]:
#     tmp_data = {}
#     tmp_data["type"] = "Feature"
#     tmp_data["id"] = data["properties"]["name"]
#     tmp_data["properties"] = data["properties"]
#     tmp_data["geometry"] = data["geometry"]
#     datas["features"].append(tmp_data)
# with open("china_state.json", "w", encoding="utf-8") as f:
#     json.dump(datas, f, ensure_ascii=False, indent=4)
labor_force = pd.read_excel("china_labor_force_2023.xlsx")
m = folium.Map(
    location=[35, 105],
    zoom_start=5,
    tiles="https://mt.google.com/vt/lyrs=r&x={x}&y={y}&z={z}",
    # tiles=
    # "https://webrd01.is.autonavi.com/appmaptile?lang=zh_cn&size=1&scale=1&style=7&x={x}&y={y}&z={z}",
    attr="google")

choropleth = folium.Choropleth(
    geo_data=geo_json_data,
    data=labor_force,
    columns=['省份', "人口(百万)"],
    key_on='id',
    fill_color='RdBu',
    use_jenks=True,
)
choropleth.add_to(m)
choropleth.color_scale.width = 800
m.save("china_state.html")  # 保存为html文件