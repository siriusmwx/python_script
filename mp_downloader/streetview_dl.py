import os
import time
import itertools
import concurrent.futures
from dataclasses import dataclass
from io import BytesIO
import requests
from PIL import Image

currend_dir = os.path.dirname(os.path.abspath(__file__))
os.chdir(currend_dir)
map_dir = os.path.join(currend_dir, "panorama")
proxys = {"http": "socks5h://127.0.0.1:1080", "https": "socks5h://127.0.0.1:1080"}


@dataclass
class TileInfo:
    x: int
    y: int
    fileurl: str


@dataclass
class Tile:
    x: int
    y: int
    image: Image.Image


def get_width_and_height_from_zoom(zoom: int):
    """
    Returns the width and height of a panorama at a given zoom level, depends on the
    zoom level.
    """
    return 2**zoom, 2**(zoom - 1)


def make_download_url(pano_id: str, zoom: int, x: int, y: int) -> str:
    """
    Returns the URL to download a tile.
    """
    return (
        f"https://streetviewpixels-pa.googleapis.com/v1/tile?cb_client=maps_sv.tactile&panoid={pano_id}&x={x}&y={y}&zoom={zoom}"
    )


def fetch_panorama_tile(tile_info: TileInfo, dl_path: str):
    """
    Tries to download a tile, returns a PIL Image.
    """
    # for _ in range(max_retries):
    while True:
        try:
            print(tile_info.fileurl)
            filepath = os.path.join(dl_path, "%s_%s.jpg" % (tile_info.x, tile_info.y))
            response = requests.get(tile_info.fileurl, proxies=proxys, stream=True)
            with open(filepath, "wb") as f:
                f.write(response.content)
            return Image.open(BytesIO(response.content))
        except requests.ConnectionError:
            print("Connection error. Trying again in 2 seconds.")
            time.sleep(2)


def iter_tile_info(pano_id: str, zoom: int):
    """
    Generate a list of a panorama's tiles and their position.
    """
    width, height = get_width_and_height_from_zoom(zoom)
    for x, y in itertools.product(range(width), range(height)):
        yield TileInfo(
            x=x,
            y=y,
            fileurl=make_download_url(pano_id=pano_id, zoom=zoom, x=x, y=y),
        )


def iter_tiles(pano_id: str, zoom: int, dl_path: str, m_thread: bool = True):
    if not m_thread:
        for info in iter_tile_info(pano_id, zoom):
            image = fetch_panorama_tile(info, dl_path)
            yield Tile(x=info.x, y=info.y, image=image)
        return

    with concurrent.futures.ThreadPoolExecutor() as executor:
        future_to_tile = {
            executor.submit(fetch_panorama_tile, info, dl_path): info
            for info in iter_tile_info(pano_id, zoom)
        }
        for future in concurrent.futures.as_completed(future_to_tile):
            info = future_to_tile[future]
            try:
                image = future.result()
            except Exception as exc:
                raise Exception(
                    f"Failed to download tile {info.fileurl} due to Exception: {exc}")
            else:
                yield Tile(x=info.x, y=info.y, image=image)


def get_panorama(pano_id: str, zoom: int = 5, m_thread: bool = True):
    """
    Downloads a streetview panorama.
    Multi-threaded is a lot faster, but it's also a lot more likely to get you banned.
    """
    tile_width = 512
    tile_height = 512
    dl_path = os.path.join(map_dir, "%s_%s" % (pano_id, 5))
    if not os.path.exists(dl_path):
        os.makedirs(dl_path)
    total_width, total_height = get_width_and_height_from_zoom(zoom)
    panorama = Image.new("RGB", (total_width * tile_width, total_height * tile_height))

    for tile in iter_tiles(pano_id=pano_id, zoom=zoom, dl_path=dl_path,
                           m_thread=m_thread):
        panorama.paste(im=tile.image, box=(tile.x * tile_width, tile.y * tile_height))
        del tile

    return panorama


if __name__ == '__main__':
    panoid = "XMthJ85wQkuUvW8rIVeTVQ"
    # panoid = "tdVgUHc3-PVfh5mjES8sjw"
    # panoid = "4nOnCr5_6hR1Jcvxu3ntPw"
    image = get_panorama(pano_id=panoid)
    image.save("%s.jpg" % panoid, "jpeg")