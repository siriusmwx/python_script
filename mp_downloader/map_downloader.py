import os
import sys
import time
import math
import requests
from PIL import Image, ImageDraw, ImageFont
import numpy as np

currend_dir = os.path.dirname(os.path.abspath(__file__))
os.chdir(currend_dir)
style = "s"
map_dir = os.path.join(currend_dir, f"{style}map")


def download(x, y, z):
    proxies = {
        "http": "socks5h://127.0.0.1:1080",
        "https": "socks5h://127.0.0.1:1080"
    }
    # url = f"https://khms0.google.com/kh/v=979?x={x}&y={y}&z={z}"
    # url = f"https://mt.google.com/vt/lyrs=s&x={x}&y={y}&z={z}"
    url = f"http://www.google.com/maps/vt?lyrs={style}@820&gl=cn&x={x}&y={y}&z={z}"
    path = os.path.join(map_dir, f"{z}{os.sep}{x}")
    filepath = os.path.join(path, f"{y}.png")
    try:
        resp = requests.get(url, proxies=proxies, stream=True)
        file_size = int(resp.headers.get('content-length', 0))
        if os.path.exists(filepath) and file_size != 0 and os.path.getsize(
                filepath) == file_size:
            print(f'{filepath} has already download.')
            return True
        if not os.path.exists(path):
            os.makedirs(path)
        print(url)
        response = requests.get(url, proxies=proxies)
        if response.status_code == 200:
            with open(filepath, "wb") as f:
                f.write(response.content)
            print(f'{filepath} download success.')
            return True
        else:
            print(f'{filepath} download failed.')
    except Exception as e:
        print(e)
        return False
    return False


def lonlat2xyz(lat, lon, zoom):
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


def latlng_dec2rad(ox):
    if ox[0] < 0:
        x = "S"
    else:
        x = "N"
    if ox[1] < 0:
        y = "W"
    else:
        y = "E"
    return f"{convert_point(ox[0])}{x} {convert_point(ox[1])}{y}"


def modifyimage(img, ox):
    txt = latlng_dec2rad(ox)
    # img = Image.open(img)
    draw = ImageDraw.Draw(img)
    imgsize = img.size
    draw_font = ImageFont.truetype('consola.ttf', imgsize[1] // 64)
    txtsize = draw_font.getbbox(txt)
    draw.rectangle(
        [txtsize[3], txtsize[3], txtsize[2] + txtsize[3], 2 * txtsize[3]],
        fill="black")
    draw.text([txtsize[3], txtsize[3]], txt, font=draw_font, fill="orange")


def merge(x1, y1, x2, y2, ox, z, mark=False):
    date = time.strftime('%Y%m%d_%H%M%S', time.localtime())
    row_list = list()
    for i in range(x1, x2 + 1):
        col_list = list()
        for j in range(y1, y2 + 1):
            img = Image.open(
                os.path.join(map_dir, f"{z}{os.sep}{i}{os.sep}{j}.png"))
            # print(img.mode)
            if img.mode != "RGB":
                img = img.convert("RGB")
            col_list.append(img)
        k = np.vstack(col_list)
        row_list.append(k)
    img_path = os.path.join(currend_dir, f"{date}.jpg")
    # final_img = Image.fromarray(255 * np.hstack(row_list).astype(np.uint8),
    #                             mode="L")
    final_img = Image.fromarray(np.hstack(row_list))
    if mark:
        modifyimage(final_img, ox)
    # final_img.show()
    final_img.save(img_path)


def map_downloader(ox, zoom=17):
    x, y = lonlat2xyz(ox[0], ox[1], zoom)
    x1, y1 = x - 8, y - 5
    x2, y2 = x + 7, y + 4
    total = (x2 - x1 + 1) * (y2 - y1 + 1)
    print(x1, y1, zoom)
    print(x2, y2, zoom)
    count = 0
    try:
        for i in range(x1, x2 + 1):
            for j in range(y1, y2 + 1):
                count += 1
                print("{m}/{n}".format(m=count, n=total))
                while not download(i, j, zoom):
                    time.sleep(5)
        merge(x1, y1, x2, y2, ox, zoom, mark=True)
    except KeyboardInterrupt:
        pass


if __name__ == '__main__':
    ox = [50.589077046992266, 30.209739847504217]
    map_downloader(ox, 18)
