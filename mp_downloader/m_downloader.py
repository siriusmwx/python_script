import os
import sys
import time
import math
import json
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
    if isinstance(txt, list):
        txt = latlng_dec2rad(txt)
    img = Image.open(img_path)
    draw = ImageDraw.Draw(img)
    imgsize = img.size
    draw_font = ImageFont.truetype('consola.ttf', imgsize[1] // 64)
    txtsize = draw_font.getbbox(txt)
    draw.rectangle(
        [txtsize[3], txtsize[3], txtsize[2] + txtsize[3], 2 * txtsize[3]],
        fill=(0, 0, 0))
    draw.text([txtsize[3], txtsize[3]], txt, font=draw_font, fill=(255, 0, 0))
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
    # modifyimage(img_path, font)


def map_downloader(title_name, zoom=17, rate=[8, 6]):
    with open("summary.json", "r", encoding="utf-8") as f:
        data = json.load(f)
    lt = data[title_name]["lt"]
    rb = data[title_name]["rb"]
    x1, y1 = lonlat2xyz(lt[0], lt[1], zoom)
    # x2, y2 = x1 + rate[0] - 1, y1 + rate[1] - 1
    x2, y2 = lonlat2xyz(rb[0], rb[1], zoom)
    # total_1 = (x3 - x1 + 1) * (y3 - y1 + 1)
    total = (x2 - x1 + 1) * (y2 - y1 + 1)
    print(f"{total}<==>{zoom}")
    count = 0
    try:
        for i in range(x1, x2 + 1):
            for j in range(y1, y2 + 1):
                download(i, j, zoom, map_dir)
                count += 1
                print("{m}/{n}".format(m=count, n=total))
                pass
        font_txt = latlng_dec2rad(lt)
        data[title_name]["odem"] = font_txt
        data[title_name]["zoom"] = zoom
        data[title_name]["rate"] = rate
        merge(x1, y1, x2, y2, zoom, map_dir, font_txt)
    except KeyboardInterrupt:
        pass
    else:
        with open("summary.json", "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)


if __name__ == '__main__':
    # ox = [-33.8656469, 151.2502086]
    # ox = [-33.8668440, 151.2516450]
    # ox = [49.2473765, -123.1938901]
    # ox = [-21.8162975, 114.1656327]
    # ox = [45.0916555, 33.5885547]
    # ox = [37.5657390, 22.7976181]
    # ox = [38.6325681, 34.8068892]
    # ox = [-22.771681837016388, -69.47967284794176]
    # print(latlng_dec2rad([50.64237656684564, -1.9232993841856219]))
    map_downloader("纽波特纽斯造船厂", int(sys.argv[1]))