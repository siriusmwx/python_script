import folium
from folium import plugins

map_osm = folium.Map(
    location=[36, 105],
    # tiles="https://www.google.cn/maps/vt?lyrs=s@815&gl=cn&x={x}&y={y}&z={z}",
    tiles="https://mt.google.com/vt/lyrs=p&x={x}&y={y}&z={z}",
    # tiles=
    # "https://wprd04.is.autonavi.com/appmaptile?lang=zh_cn&size=1&style=7&x={x}&y={y}&z={z}",
    zoom_start=5,
    attr="Google")  #绘制Map，开始缩放程度是5倍
map_osm.add_child(folium.LatLngPopup())
map_osm.add_child(plugins.MeasureControl())
plugins.Geocoder().add_to(map_osm)
map_osm.save("osm.html")  # 保存为html文件