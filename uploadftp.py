#!/usr/bin/env python3
import re
import os
import sys
import time
from pathlib import Path
from shutil import move, SameFileError
from ftplib import FTP


def get_mtime(file):
    date = time.localtime(os.path.getmtime(file))
    return time.strftime('%Y%m%d', date)


def move_file(file, dst):
    dst.mkdir(exist_ok=True)
    try:
        move(str(file), str(dst))
        print('Upload %s to ftp server and move to %s' % (file, dst))
    except SameFileError:
        pass


class LogBackup(FTP):

    file_ext = re.compile(r'(app\.log|boot\.log|phone.cfg|\.csv)$', re.I)
    hostname = '172.24.255.212'
    username = 'logbackup'
    password = 'pega#$34'

    def __init__(self, model_name, station_name, device_id):
        self.port = 2100
        # self.debugging = 1
        self.encoding = 'gbk'
        self.model_name = model_name
        self.station_name = station_name
        self.device_id = device_id
        super().__init__(host=self.hostname, user=self.username, passwd=self.password)
        print(self.getwelcome())

    def change_dir(self, dirname):
        try:
            self.mkd(dirname)
        except:
            pass
        finally:
            self.cwd(dirname)

    def uploadfile(self, remotepath, localpath):
        # bufsize = 1024
        try:
            with open(localpath, 'rb') as f:
                self.storbinary('STOR %s' % remotepath, f)
        except:
            return False
        return True

    def downloadfile(self, remotepath, localpath):
        # bufsize = 1024
        try:
            with open(localpath, 'wb') as f:
                self.retrbinary('RETR %s' % remotepath, f.write)
        except:
            return False
        return True

    def upload_to_ftp(self, log_dir, backup_dir):
        log_path = Path(log_dir)
        if not log_path.is_dir():
            return
        backup_path = Path(backup_dir)
        backup_path.mkdir(exist_ok=True)
        print('Starting backup %s logs to %s.' % (log_path, backup_path))
        self.change_dir('/IPPHONE/')
        self.change_dir(self.model_name)
        self.change_dir(self.station_name)
        self.change_dir(self.device_id)
        for file in log_path.glob('*'):
            if file.is_file():
                if self.file_ext.search(str(file)):
                    date_dir = get_mtime(file)
                    self.change_dir(date_dir)
                    filename = os.path.basename(file)
                    if self.uploadfile(filename, file):
                        restore_dir = Path(backup_path, date_dir)
                        move_file(file, restore_dir)
                    self.change_dir('..')


if __name__ == '__main__':
    config = {
        'model_name': 'GS560',
        'station_name': 'FCT2',
        'device_id': '203959',
        'log_path': {
            r'C:\APPLOGBACKUP': r'D:\CCX_600',
            r'C:\Inetpub\ftproot': r'D:\CCX_700'
        },
    }
    try:
        logbackup = LogBackup(config['model_name'],
                              config['station_name'],
                              config['device_id'])
    except Exception as e:
        sys.exit(e)
    try:
        for key in config['log_path']:
            logbackup.upload_to_ftp(key, config['log_path'][key])
    except Exception as e:
        print(e)
    finally:
        logbackup.close()
