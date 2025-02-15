#!/usr/bin/python3
import re
import os
import sys
import base64
import shutil
import requests
from pathlib import Path
from tqdm import tqdm
from Crypto.Cipher import AES
from subprocess import run, DEVNULL

current_dir = os.path.dirname(os.path.abspath(__file__))
os.chdir(current_dir)

# ffmpeg -i 1923_S01E01.mkv -ss 00:57:18 -t 00:02:10 -c:v copy -c:a copy 1923_S01E01_1.mkv
# ffmpeg -i 1923_S01E01.mkv -ss 00:57:18 -t 00:02:10 -c:v libx264 -c:a libfaac 1923_S01E01_2.mkv
# ffmpeg -ss 00:57:08 -t 00:02:20 -i 1923_S01E01.mkv -vcodec copy -acodec copy 1923_S01E01_1.mp4
# ffmpeg -i 1923_S01E01_0.mkv -vcodec copy -acodec aac 1923_S01E01_0.mp4
# ffmpeg -ss 00:47:20 -t 00:00:40 -i output.mp4 -vcodec copy -acodec copy output_1.mp4
# ffmpeg -i videoplayback.mp4 -i videoplayback.m4a -vcodec copy -acodec copy videoplayback_c.mp4
# ffmpeg -i Northern_Lights.mp4 -vcodec copy -an Northern_Lights1.mp4
# ffmpeg -i 3.mp4 -acodec copy -vn 3.m4a
# ffmpeg -f concat -i aa.txt -c copy alexhook.mp4


class VideoDownloader:
    """
    tw-dl offers the ability to download videos from Video feeds.
    """
    def __init__(self, m3u8_p="", proxy=True):
        with open(m3u8_p) as f:
            self.txt = f.read()
            # self.ts_files = re.findall(r'[a-zA-Z0-9_-]+\.ts$', txt, re.M)
        self.ts_files = re.findall('[0-9a-z]+\.ts', self.txt, re.M)
        print(self.ts_files)
        self.urls = re.findall('^https:.*[0-9a-z]+\.ts.*$', self.txt, re.M)
        print(self.urls)
        # iv = base64.b64encode("2752908e707c71d8806b2ae6bb03fc1f")
        # print(iv)
        with open("crypt.key", "rb") as f:
            self.decrypter = AES.new(f.read(), AES.MODE_CBC, "2752908e707c71d8".encode())
        self.name = m3u8_p.split('.')[0]
        storage_dir = Path(self.name)
        storage_dir.mkdir(parents=True, exist_ok=True)
        self.storage_dir = str(storage_dir.resolve())
        self.request = requests.Session()
        if proxy:
            # - SOCKS4A (``proxy_url='socks4a://...``)
            # - SOCKS4 (``proxy_url='socks4://...``)
            # - SOCKS5 with remote DNS (``proxy_url='socks5h://...``)
            # - SOCKS5 with local DNS (``proxy_url='socks5://...``)
            self.request.proxies = {
                'http': 'socks5h://127.0.0.1:1080',
                'https': 'socks5h://127.0.0.1:1080'
            }
            print('Using proxy with socks5://127.0.0.1:1080')
            # import socks
            # import socket
            # socks.set_default_proxy(socks.SOCKS5, '127.0.0.1', 1080)
            # socket.socket = socks.socksocket # does not works

    def download(self):
        ts_full_file = Path(self.storage_dir, self.name + '.ts')
        video_file = Path(self.storage_dir, self.name + '.mp4')
        ts_list = []
        for index, ts in enumerate(self.ts_files):
            print('Downloading %s' % ts)
            ts_path = Path(self.storage_dir, ts)
            ts_list.append(ts_path)
            resp = self.request.get(self.urls[index], stream=True)
            file_size = int(resp.headers.get('content-length', 0))
            if ts_path.exists() and file_size != 0 and ts_path.stat(
            ).st_size == file_size:
                print('%s has already download.' % ts)
                continue
            p_bar = tqdm(total=file_size, unit='iB', colour='green', unit_scale=True)
            with open(ts_path, 'wb') as file:
                for data in resp.iter_content(chunk_size=1024):
                    p_bar.update(len(data))
                    file.write(self.decrypter.decrypt(data))
            p_bar.close()
            if file_size != 0 and p_bar.n != file_size:
                print("ERROR, something went wrong")
        print('compress %s all ts in one' % len(ts_list))
        with open(str(ts_full_file), 'wb') as wfd:
            for ts_p in ts_list:
                with open(str(ts_p), 'rb') as fd:
                    shutil.copyfileobj(fd, wfd, 1024 * 1024 * 10)
        print('Convert %s.ts to %s.mp4' % (self.name, self.name))
        cmd = 'ffmpeg -y -i %s -acodec copy -vcodec copy -f mp4 %s' % (ts_full_file,
                                                                       video_file)
        proc = run(cmd, capture_output=True, shell=True)
        if proc.returncode != 0:
            print('Convert %s.ts to %s.mp4 failed' % (self.name, self.name))
        # print('Start clean ts files...')
        # [ts.unlink() for ts in ts_list]


def main(m3u8_file):
    video_dl = VideoDownloader(m3u8_p=m3u8_file, proxy=False)
    video_dl.download()


if __name__ == '__main__':
    main("example.m3u8")
