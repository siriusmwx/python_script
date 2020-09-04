#!/usr/bin/env python3
import re
import json
import m3u8
import shutil
import logging
import argparse
import requests
import fileinput
import urllib.parse
from pathlib import Path
from subprocess import run, DEVNULL

data_format = "%d %b %Y %H:%M:%S"
msg_format = "<<%(asctime)s><%(name)s><%(levelname)s><%(message)s"
sto_format = "[%(levelname)s]:%(message)s"


def handler(filename=None,  filemode='a', backup=False,
            stream=None, msg_fmt=None, data_fmt=None):
    if filename:
        if backup:
            from logging.handlers import RotatingFileHandler
            handler = RotatingFileHandler(
                filename, maxBytes=1024 * 1024 * 10, backupCount=3)
        else:
            handler = logging.FileHandler(filename, mode=filemode)
    else:
        handler = logging.StreamHandler(stream=stream)
    if msg_fmt:
        formatter = logging.Formatter(fmt=msg_fmt, datefmt=data_fmt)
        handler.setFormatter(formatter)
    return handler


def logger(name=None, handler=None, level=logging.DEBUG):
    logger = logging.getLogger(name)
    logger.setLevel(level)
    if handler:
        logger.addHandler(handler)
    return logger


class TwitterDownloader:
    """
    tw-dl offers the ability to download videos from Twitter feeds.
    """
    tweet_data = {}
    video_player_prefix = 'https://twitter.com/i/videos/tweet/'
    video_api = 'https://api.twitter.com/1.1/videos/tweet/config/'

    log_handler = handler('download.log', backup=True,
                          msg_fmt=msg_format, data_fmt=data_format)
    sto_handler = handler(msg_fmt=sto_format)
    my_loger = logger(name='TwitterDownloader', handler=log_handler)
    sto_logger = logger(name='Debug_Info', handler=sto_handler)
    sto_logger.addHandler(log_handler)

    def __init__(self, tweet_url, output_dir='output', proxy=False):
        """
        We split on ? to clean up the URL. Sharing tweets, for example,
        will add ? with data about which device shared it.
        The rest is just getting the user and ID to work with.
        """
        # self.debug = debug
        self.tweet_data['tweet_url'] = tweet_url.split('?', 1)[0]
        self.tweet_data['user'] = self.tweet_data['tweet_url'].split('/')[3]
        self.tweet_data['id'] = self.tweet_data['tweet_url'].split('/')[5]

        storage_dir = Path(output_dir, self.tweet_data['user'])
        storage_dir.mkdir(parents=True, exist_ok=True)
        self.storage_dir = str(storage_dir.resolve())

        self.request = requests.Session()
        if proxy:
            # - SOCKS4A (``proxy_url='socks4a://...``)
            # - SOCKS4 (``proxy_url='socks4://...``)
            # - SOCKS5 with remote DNS (``proxy_url='socks5h://...``)
            # - SOCKS5 with local DNS (``proxy_url='socks5://...``)
            self.request.proxies = {'http': 'socks5h://127.0.0.1:1080',
                                    'https': 'socks5h://127.0.0.1:1080'}
            self.sto_logger.debug('Using proxy with socks5://127.0.0.1:1080')
            # import socks
            # import socket
            # socks.set_default_proxy(socks.SOCKS5, '127.0.0.1', 1080)
            # socket.socket = socks.socksocket # does not works

    def download(self):
        self.sto_logger.debug('Tweet URL:' + self.tweet_data['tweet_url'])

        # Get the bearer token
        token = self.__get_bearer_token()

        # Get the M3u8 file - this is where rate limiting has been happening
        video_host, playlist = self.__get_playlist(token)
        if playlist.is_variant:
            playlists = playlist.playlists
            playlists.sort(
                key=lambda p: p.stream_info.resolution[0], reverse=True)
            resolution = playlists[0].stream_info.resolution
            self.sto_logger.debug('%s resolutions found. Slurping %sx%s resolution.' %
                                  (len(playlists), resolution[0], resolution[1]))
            self.__parse_videos(video_host, playlists[0])
        else:
            self.sto_logger.error(
                'Sorry, single resolution video download is not yet implemented.')
            self.sto_logger.error(
                'Please submit a bug report with the link to the tweet.')

    def __parse_videos(self, video_host, playlist):
        playlist_url = video_host + playlist.uri
        self.sto_logger.debug('Play_list Url:' + playlist_url)
        match = re.search(
            '/([^/]+)/([^/]+).m3u8', playlist_url)
        video_name = match.group(2) + '_' + match.group(1)
        video_file = Path(self.storage_dir, video_name + '.mp4')
        ts_full_file = Path(self.storage_dir, video_name + '.ts')

        self.sto_logger.debug('Downloading ' + video_name + '.mp4')
        resp = self.request.get(
            playlist_url, headers={'Authorization': None}).text
        self.my_loger.info('Request M3U8:' + resp)
        ts_m3u8_parse = m3u8.loads(resp)
        ts_list = []
        for ts_uri in ts_m3u8_parse.segments.uri:
            ts_file = self.request.get(video_host + ts_uri)
            self.my_loger.info('TS Url:' + video_host + ts_uri)
            fname = ts_uri.split('/')[-1]
            ts_path = Path(self.storage_dir, fname)
            ts_list.append(ts_path)
            ts_path.write_bytes(ts_file.content)

        with open(str(ts_full_file), 'wb') as wfd:
            for ts in ts_list:
                with open(str(ts), 'rb') as fd:
                    shutil.copyfileobj(fd, wfd, 1024 * 1024 * 10)

        self.sto_logger.debug('\tDoing the magic ...')
        ffmpeg = Path('ffmpeg').resolve()
        # cmd = '%s -y -i %s -c:v libx264 -c:a copy -bsf:a aac_adtstoasc %s' % (
        #     ffmpeg, ts_full_file, video_file)
        cmd = '%s -y -i %s -acodec copy -vcodec copy -f mp4 %s' % (
            ffmpeg, ts_full_file, video_file)
        proc = run(cmd, stdout=DEVNULL, stderr=DEVNULL, shell=True)

        self.sto_logger.debug('\tDoing cleanup...')
        [ts.unlink() for ts in ts_list]
        ts_full_file.unlink()

    def __get_bearer_token(self):
        video_player_url = self.video_player_prefix + self.tweet_data['id']
        self.sto_logger.debug('Video Player Url:' + video_player_url)
        resp = self.request.get(video_player_url).text
        self.my_loger.info('Video Player Body:' + resp)

        js_file_url = re.search('src="(.*js)"', resp).group(1)
        self.sto_logger.debug('JS File Url:' + js_file_url)
        resp = self.request.get(js_file_url).text
        self.my_loger.info('JS File Body:' + resp)
        bearer_token = re.search('Bearer ([a-zA-Z0-9%-])+', resp).group(0)
        self.request.headers.update({'Authorization': bearer_token})
        self.sto_logger.debug('Update Authorization:' + bearer_token)
        self.__get_guest_token()

        return bearer_token

    def __get_playlist(self, token):
        resp = self.request.get(
            self.video_api + self.tweet_data['id'] + '.json').text
        self.sto_logger.debug('Video Api Url:' + self.video_api +
                              self.tweet_data['id'] + '.json')
        self.my_loger.info('Player Config:' + resp)
        player_config = json.loads(resp)

        if 'errors' not in player_config:
            self.my_loger.info('Player Config JSON:' +
                               json.dumps(player_config))
            m3u8_url = player_config['track']['playbackUrl']
            self.sto_logger.debug('M3U8 Url:' + m3u8_url)
        else:
            self.sto_logger.error(
                'Player Config JSON - Error' + json.dumps(player_config['errors']))
            self.sto_logger.error(
                'Rate limit exceeded. Could not recover. Try again later.')
            exit(1)

        # Get m3u8
        resp = self.request.get(m3u8_url).text
        self.my_loger.info('M3U8 Response:' + resp)

        m3u8_url_parse = urllib.parse.urlparse(m3u8_url)
        video_host = m3u8_url_parse.scheme + '://' + m3u8_url_parse.hostname
        self.sto_logger.debug('Video Host:' + video_host)
        m3u8_parse = m3u8.loads(resp)

        return video_host, m3u8_parse

    def __get_guest_token(self):
        res = self.request.post(
            "https://api.twitter.com/1.1/guest/activate.json").text
        self.sto_logger.debug(
            'Request Post:https://api.twitter.com/1.1/guest/activate.json')
        self.my_loger.info(res)
        res_json = json.loads(res)
        self.request.headers.update(
            {'x-guest-token': res_json.get('guest_token')})
        self.sto_logger.debug(
            'Update x-guest-token:' + res_json.get('guest_token'))
        self.my_loger.info('Request Header:' + str(self.request.headers))

    # def __debug(self, msg_prefix, msg_body, msg_body_full=''):
    #     if self.debug == 0:
    #         return

    #     if self.debug == 1:
    #         print('[Debug] ' + '[' + msg_prefix + ']' + ' ' + msg_body)

    #     if self.debug == 2:
    #         print('[Debug+] ' + '[' + msg_prefix + ']' +
    #               ' ' + msg_body + ' - ' + msg_body_full)


def main():
    parser = argparse.ArgumentParser(
        description='Download Twitter video streams')
    url_parser = parser.add_mutually_exclusive_group()
    url_parser.add_argument('--url', metavar='twitter_url',
                            help='The twitter_video_url(https://twitter.com/<user>/status/<id>).')
    url_parser.add_argument('--url_list', metavar='url.txt',
                            help='The file with the url lists of the twitter videos')
    parser.add_argument('-o', '--output', default='output',
                        help='The directory to download videos.(<output>/<user>/)')
    # parser.add_argument('-d', '--debug', choices=[0, 1, 2], default=1, type=int,
    # help='Debug level. Show more information of response bodies.')
    parser.add_argument('-p', '--proxy', action='store_true',
                        help='Download video with socks5 proxy,default=127.0.0.1:1080.')
    args = parser.parse_args()
    if args.url:
        twitter_dl = TwitterDownloader(args.url, args.output, args.proxy)
        twitter_dl.download()
    elif args.url_list:
        url_list = []
        for url in fileinput.input(args.url_list, inplace=True):
            url = url.rstrip()
            if url.startswith('https://twitter.com'):
                if len(url_list) < 5:
                    url_list.append(url)
                    url = '# ' + url
            print(url)
        print(url_list)
        for url in url_list:
            twitter_dl = TwitterDownloader(url, args.output, args.proxy)
            twitter_dl.download()
    else:
        parser.print_help()


if __name__ == '__main__':
    main()
