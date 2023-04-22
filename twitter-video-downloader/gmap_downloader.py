import os
import sys
import time
import math
import requests
import cv2
import numpy as np

currend_dir = os.path.dirname(os.path.abspath(__file__))
os.chdir(currend_dir)
map_dir = os.path.join(currend_dir, "map")


def download(x, y, z, path):
    proxies = {
        "http": "socks5h://127.0.0.1:1080",
        "https": "socks5h://127.0.0.1:1080"
    }
    url = f"https://mt.google.com/vt/lyrs=s&x={x}&y={y}&z={z}"
    path = os.path.join(path, f"{z}/{x}")
    filepath = os.path.join(path, f"{y}.png")
    resp = requests.get(url, proxies=proxies, stream=True)
    file_size = int(resp.headers.get('content-length', 0))
    if os.path.exists(filepath) and file_size != 0 and os.path.getsize(
            filepath) == file_size:
        print(f'{filepath} has already download.')
        return
    if not os.path.exists(path):
        os.makedirs(path)
    for x in range(0, 3):
        response = requests.get(url, proxies=proxies)
        if response.status_code == 200:
            with open(filepath, "wb") as f:
                f.write(response.content)
            print(f'{filepath} download success.')
            return
        else:
            print(f'{filepath} download failed.')


def xyz2lonlat(x, y, z):
    n = math.pow(2, z)
    lon = x / n * 360.0 - 180.0
    lat = math.atan(math.sinh(math.pi * (1 - 2 * y / n)))
    lat = lat * 180.0 / math.pi
    return lon, lat


def lonlat2xyz(lon, lat, zoom):
    n = math.pow(2, zoom)
    x = ((lon + 180) / 360) * n
    y = (1 - (math.log(
        math.tan(math.radians(lat)) +
        (1 / math.cos(math.radians(lat)))) / math.pi)) / 2 * n
    return int(x), int(y)


def latlng_dec2rad(decnum):
    degree = int(decnum)  #度
    numdecimal = abs(decnum - degree)
    tmp = numdecimal * 3600
    minute = int(tmp // 60)  #分
    # second = int(tmp - minute * 60)  #秒
    return f"{degree}_{minute}"


def map_downloader(ox, zoom=17):
    lt = [ox[0] + 0.004, ox[1] - 0.008]
    rb = [ox[0] - 0.004, ox[1] + 0.008]
    x1, y1 = lonlat2xyz(lt[1], lt[0], zoom)
    x2, y2 = lonlat2xyz(rb[1], rb[0], zoom)
    print(x1, y1, zoom)
    print(x2, y2, zoom)
    count = 0
    all = (x2 - x1 + 1) * (y2 - y1 + 1)
    for i in range(x1, x2 + 1):
        for j in range(y1, y2 + 1):
            download(i, j, zoom, map_dir)
            count += 1
            print("{m}/{n}".format(m=count, n=all))
            pass
    merge(x1, y1, x2, y2, zoom, map_dir)


def merge(x1, y1, x2, y2, z, path):
    date = time.strftime('%Y%m%d%H%M%S', time.localtime())
    row_list = list()
    for i in range(x1, x2 + 1):
        col_list = list()
        for j in range(y1, y2 + 1):
            col_list.append(cv2.imread(os.path.join(path, f"{z}/{i}/{j}.png")))
        k = np.vstack(col_list)
        row_list.append(k)
    result = np.hstack(row_list)
    cv2.imwrite(
        os.path.join(
            path,
            f"{latlng_dec2rad(ox[0])}_{latlng_dec2rad(ox[1])}_{date}.png"),
        result)


if __name__ == '__main__':
    # ox = [-33.8656469, 151.2502086]
    # ox = [-33.8668440, 151.2516450]
    ox = [49.2473765, -123.1938901]
    map_downloader(ox, int(sys.argv[1]))