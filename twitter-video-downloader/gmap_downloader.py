import math
import os
import requests
import cv2
import numpy as np

currend_dir = os.path.dirname(os.path.abspath(__file__))
os.chdir(currend_dir)


def download(x, y, z, path):
    proxies = {
        "http": "socks5h://127.0.0.1:1080",
        "https": "socks5h://127.0.0.1:1080"
    }
    url = f"https://mt.google.com/vt/lyrs=s&x={x}&y={y}&z={z}"
    path = os.path.join(path, f"{z}/{x}")
    if not os.path.exists(path):
        os.makedirs(path)
    filepath = os.path.join(path, f"{y}.png")
    for x in range(0, 3):
        response = requests.get(url, proxies=proxies)
        if response.status_code == 200:
            with open(filepath, "wb") as f:
                f.write(response.content)
            break
        else:
            print("network error!")


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


def cal_tiff_box(x1, y1, x2, y2, z):
    LT = xyz2lonlat(x1, y1, z)
    RB = xyz2lonlat(x2 + 1, y2 + 1, z)
    return Point(LT[0], LT[1]), Point(RB[0], RB[1])


def core(z):
    path = "map"
    # lt = [-33.8656469, 151.2502086]
    # rb = [-33.8806469, 151.2652086]
    ox = [-33.8656469, 151.2502086]
    lt = [ox[0] + 0.0035, ox[1] - 0.0075]
    rb = [ox[0] - 0.0035, ox[1] + 0.0075]
    x1, y1 = lonlat2xyz(lt[1], lt[0], z)
    x2, y2 = lonlat2xyz(rb[1], rb[0], z)
    print(x1, y1, z)
    print(x2, y2, z)
    count = 0
    all = (x2 - x1 + 1) * (y2 - y1 + 1)
    for i in range(x1, x2 + 1):
        for j in range(y1, y2 + 1):
            download(i, j, z, path)
            count += 1
            print("{m}/{n}".format(m=count, n=all))
            pass
    merge(x1, y1, x2, y2, z, path)


def merge(x1, y1, x2, y2, z, path):
    row_list = list()
    for i in range(x1, x2 + 1):
        col_list = list()
        for j in range(y1, y2 + 1):
            col_list.append(cv2.imread(os.path.join(path, f"{z}/{i}/{j}.png")))
        k = np.vstack(col_list)
        row_list.append(k)
    result = np.hstack(row_list)
    cv2.imwrite(os.path.join(path, "merge.png"), result)


if __name__ == '__main__':
    core(z=17)  #调整下载级别
