import os
import sys
import time
import math
import requests
from PIL import Image, ImageDraw, ImageFont
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
    path = os.path.join(path, f"{z}{os.sep}{x}")
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


def lonlat2xyz(lon, lat, zoom):
    n = math.pow(2, zoom)
    x = ((lon + 180) / 360) * n
    y = (1 - (math.log(
        math.tan(math.radians(lat)) +
        (1 / math.cos(math.radians(lat)))) / math.pi)) / 2 * n
    return int(x), int(y)


def convert_point(point):
    point = abs(point)
    degree = int(point)  #度
    numdecimal = point - degree
    tmp = numdecimal * 3600
    minute = int(tmp // 60)  #分
    second = int(tmp - minute * 60)  #秒
    return f"{degree}°{minute:02}′{second:02.0f}″"


def latlng_dec2rad(decnum):
    if decnum[0] < 0:
        x = "S"
    else:
        x = "N"
    if decnum[1] < 0:
        y = "W"
    else:
        y = "E"
    return f"{convert_point(decnum[0])}{x} {convert_point(decnum[1])}{y}"


def modifyimage(img_path, txt):
    img = Image.open(img_path)
    draw = ImageDraw.Draw(img)
    imgsize = img.size
    draw_font = ImageFont.truetype('consola.ttf', imgsize[1] // 64)
    txtsize = draw_font.getsize(txt)
    x = txtsize[1] / 2
    y = imgsize[1] - 3 * txtsize[1] / 2
    draw.text([x, y], txt, font=draw_font)
    img.save(img_path)


def merge(x1, y1, x2, y2, z, path, font):
    date = time.strftime('%Y%m%d_%H%M%S', time.localtime())
    row_list = list()
    for i in range(x1, x2 + 1):
        col_list = list()
        for j in range(y1, y2 + 1):
            col_list.append(
                Image.open(os.path.join(path,
                                        f"{z}{os.sep}{i}{os.sep}{j}.png")))
        k = np.vstack(col_list)
        row_list.append(k)
    img_path = os.path.join(currend_dir, f"{date}.jpg")
    final_pic = Image.fromarray(np.hstack(row_list))
    final_pic.save(img_path)
    modifyimage(img_path, font)


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
    font_txt = latlng_dec2rad(ox)
    merge(x1, y1, x2, y2, zoom, map_dir, font_txt)


if __name__ == '__main__':
    # ox = [-33.8656469, 151.2502086]
    # ox = [-33.8668440, 151.2516450]
    # ox = [49.2473765, -123.1938901]
    # ox = [-21.8162975, 114.1656327]
    # ox = [45.0916555, 33.5885547]
    # ox = [37.5657390, 22.7976181]
    ox = [38.6325681, 34.8068892]
    map_downloader(ox, int(sys.argv[1]))