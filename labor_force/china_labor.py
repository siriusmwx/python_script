import json
import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt

df = pd.read_excel('china_labor_force_2023.xlsx')
geo_df = gpd.GeoDataFrame.from_file('china.json')
geo_df = geo_df[["name", "geometry"]]
with open("china.json", encoding="utf-8") as f:
    datas = json.load(f)
total_data = []
for data in datas["features"]:
    tp = {}
    tp["name"] = data["properties"]["name"]
    tp["center"] = data["properties"]["cp"]
    total_data.append(tp)
geo_df = pd.merge(geo_df, pd.DataFrame(total_data), how='left')
labor_force2023 = pd.merge(geo_df,
                           df,
                           left_on='name',
                           right_on='省份',
                           how='left')
del labor_force2023['name']  # 删除多余字段，这里存在重复字段，删除一个
labor_force2023 = labor_force2023.sort_values(by='人口(百万)', ascending=False)
print(labor_force2023.head())
plt.rcParams['font.family'] = 'SimHei'
plt.figure(figsize=(16, 12))
plt.title('2023 全国各省人口统计（百万）', fontsize=20)
plt.grid(True, alpha=0.5)  # 设置网格线
# 绘制人口地图
labor_force2023.plot(ax=plt.subplot(1, 1, 1),
                     alpha=1,
                     edgecolor='k',
                     linewidth=0.5,
                     legend=True,
                     scheme='FisherJenks',
                     column='人口(百万)',
                     cmap='BuGn')
for index, row in labor_force2023.iterrows():
    if "香港" in row["省份"]:
        plt.text(row["center"][0],
                 row["center"][1] - 1,
                 "香港\n%s" % row["人口(百万)"],
                 fontsize=10)
    elif "澳门" in row["省份"]:
        plt.text(row["center"][0],
                 row["center"][1] - 1,
                 "澳门\n%s" % row["人口(百万)"],
                 fontsize=10)
    else:
        plt.text(row["center"][0],
                 row["center"][1],
                 "%s\n%s%s" % (row["省份"], " " *
                               (len(row["省份"]) // 2), row["人口(百万)"]),
                 fontsize=10)
plt.savefig('demo.png', dpi=300)