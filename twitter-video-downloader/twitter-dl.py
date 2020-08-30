#!/usr/bin/env python
import re
import json
import m3u8
import shutil
import argparse
import requests
import urllib.parse
from pathlib import Path
from subprocess import run


class TwitterDownloader:
    """
    tw-dl offers the ability to download videos from Twitter feeds.
    """
    tweet_data = {}
    video_player_prefix = 'https://twitter.com/i/videos/tweet/'
    video_api = 'https://api.twitter.com/1.1/videos/tweet/config/'

    def __init__(self, tweet_url, output_dir='output', debug=0):
        """
        We split on ? to clean up the URL. Sharing tweets, for example,
        will add ? with data about which device shared it.
        The rest is just getting the user and ID to work with.
        """
        self.debug = debug
        self.tweet_data['tweet_url'] = tweet_url.split('?', 1)[0]
        self.tweet_data['user'] = self.tweet_data['tweet_url'].split('/')[3]
        self.tweet_data['id'] = self.tweet_data['tweet_url'].split('/')[5]

        storage_dir = Path(output_dir) / self.tweet_data['user']
        Path.mkdir(storage_dir, parents=True, exist_ok=True)
        self.storage_dir = str(storage_dir)

        self.request = requests.Session()
        # self.request.proxies = {'http': 'socks5://127.0.0.1:1080',
        #                         'https': 'socks5://127.0.0.1:1080'}

    def download(self):
        self.__debug('Tweet URL', self.tweet_data['tweet_url'])

        # Get the bearer token
        token = self.__get_bearer_token()

        # Get the M3u8 file - this is where rate limiting has been happening
        video_host, playlist = self.__get_playlist(token)
        if playlist.is_variant:
            playlists = playlist.playlists
            playlists.sort(
                key=lambda p: p.stream_info.resolution[0], reverse=True)
            resolution = playlists[0].stream_info.resolution
            print('[+] %s resolutions found. Slurping %sx%s resolution.' %
                  (len(playlists), resolution[0], resolution[1]))
            self.__parse_videos(video_host, playlists[0])
        else:
            print('[!] Sorry, single resolution video download is not yet implemented.')
            print('    Please submit a bug report with the link to the tweet.')

    def __parse_videos(self, video_host, playlist):
        playlist_url = video_host + playlist.uri
        match = re.search(
            '/([^/]+)/([^/]+).m3u8', playlist_url)
        video_name = match.group(2) + '_' + match.group(1)
        video_file = str(Path(self.storage_dir) /
                         Path(video_name + '.mp4'))
        ts_full_file = str(Path(self.storage_dir) /
                           Path(video_name + '.ts'))

        print('[+] Downloading ' + video_name + '.mp4')
        resp = self.request.get(
            playlist_url, headers={'Authorization': None})
        ts_m3u8_parse = m3u8.loads(resp.text)
        ts_list = []
        for ts_uri in ts_m3u8_parse.segments.uri:
            ts_file = self.request.get(video_host + ts_uri)
            fname = ts_uri.split('/')[-1]
            ts_path = Path(self.storage_dir) / Path(fname)
            ts_list.append(ts_path)
            ts_path.write_bytes(ts_file.content)

        with open(ts_full_file, 'wb') as wfd:
            for f in ts_list:
                with open(f, 'rb') as fd:
                    shutil.copyfileobj(fd, wfd, 1024 * 1024 * 10)

        print('\t[*] Doing the magic ...')
        # cmd = 'ffmpeg -y -i %s -c:v libx264 -c:a copy -bsf:a aac_adtstoasc %s' % (
        #     ts_full_file, video_file)
        cmd = 'ffmpeg -y -i %s -acodec copy -vcodec copy -f mp4 %s' % (
            ts_full_file, video_file)
        proc = run(cmd, capture_output=True, shell=True)

        print('\t[+] Doing cleanup...')
        [Path(ts).unlink() for ts in ts_list]
        Path(ts_full_file).unlink()

    def __get_bearer_token(self):
        video_player_url = self.video_player_prefix + self.tweet_data['id']
        resp = self.request.get(video_player_url).text
        self.__debug('Video Player Body', '', resp)

        js_file_url = re.search('src="(.*js)"', resp).group(1)
        resp = self.request.get(js_file_url).text
        self.__debug('JS File Body', '', resp)

        bearer_token = re.search('Bearer ([a-zA-Z0-9%-])+', resp).group(0)
        self.request.headers.update({'Authorization': bearer_token})
        self.__debug('Bearer Token', bearer_token)
        self.__get_guest_token()

        return bearer_token

    def __get_playlist(self, token):
        resp = self.request.get(
            self.video_api + self.tweet_data['id'] + '.json')
        player_config = json.loads(resp.text)

        if 'errors' not in player_config:
            self.__debug('Player Config JSON', '', json.dumps(player_config))
            m3u8_url = player_config['track']['playbackUrl']
        else:
            self.__debug('Player Config JSON - Error',
                         json.dumps(player_config['errors']))
            print('[!] Rate limit exceeded. Could not recover. Try again later.')
            exit(1)

        # Get m3u8
        resp = self.request.get(m3u8_url).text
        self.__debug('M3U8 Response', '', resp)

        m3u8_url_parse = urllib.parse.urlparse(m3u8_url)
        video_host = m3u8_url_parse.scheme + '://' + m3u8_url_parse.hostname

        m3u8_parse = m3u8.loads(resp)

        return video_host, m3u8_parse

    def __get_guest_token(self):
        """
        Thanks to @devkarim for this fix: 
        https://github.com/h4ckninja/twitter-video-downloader/issues/2#issuecomment-538773026
        """
        res = self.request.post(
            "https://api.twitter.com/1.1/guest/activate.json")
        res_json = json.loads(res.text)
        self.request.headers.update(
            {'x-guest-token': res_json.get('guest_token')})

    def __debug(self, msg_prefix, msg_body, msg_body_full=''):
        if self.debug == 0:
            return

        if self.debug == 1:
            print('[Debug] ' + '[' + msg_prefix + ']' + ' ' + msg_body)

        if self.debug == 2:
            print('[Debug+] ' + '[' + msg_prefix + ']' +
                  ' ' + msg_body + ' - ' + msg_body_full)


def main():
    parser = argparse.ArgumentParser(
        description='Download Twitter video streams')
    parser.add_argument('tweet_url',
                        help='The twitter video URL(https://twitter.com/<user>/status/<id>).')
    parser.add_argument('-o', '--output', default='output',
                        help='The directory to download videos.(<output>/<user>/)')
    parser.add_argument('-d', '--debug', choices=[0, 1, 2], default=1, type=int,
                        help='Debug level. Show more information of response bodies.')
    args = parser.parse_args()
    twitter_dl = TwitterDownloader(args.tweet_url, args.output, args.debug)
    twitter_dl.download()

if __name__ == '__main__':
    main()
