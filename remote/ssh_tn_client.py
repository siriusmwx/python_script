# -*- coding:utf-8 -*-
import os
import sys
import time
import re
import logging
import paramiko
from telnetlib import Telnet

currend_dir = os.path.dirname(os.path.abspath(__file__))
os.chdir(currend_dir)
msg_format = "[ %(levelname)s %(asctime)s ] %(message)s"


def log_handler(filename=None,
                filemode='a',
                backup=False,
                stream=None,
                msg_fmt=None,
                date_fmt=None):
    if filename:
        if backup:
            from logging.handlers import RotatingFileHandler
            handler = RotatingFileHandler(filename,
                                          maxBytes=2048000,
                                          backupCount=10,
                                          encoding='utf-8')
        else:
            handler = logging.FileHandler(filename,
                                          mode=filemode,
                                          encoding='utf-8')
    else:
        handler = logging.StreamHandler(stream=stream)
    if msg_fmt:
        formatter = logging.Formatter(fmt=msg_fmt, datefmt=date_fmt)
        handler.setFormatter(formatter)
    return handler


def logger(name=None, handler=None, level=logging.DEBUG):
    logger = logging.getLogger(name)
    logger.setLevel(level)
    if handler:
        logger.addHandler(handler)
    return logger


date = time.strftime('%Y%m%d%H%M%S', time.localtime())
file_handler = log_handler(
    '%s_%s.log' % (os.path.splitext(os.path.basename(__file__))[0], date),
    backup=True,
    msg_fmt=msg_format)
std_handler = log_handler(msg_fmt=msg_format)
my_loger = logger(name='local_upgrade', handler=std_handler)
my_loger.addHandler(file_handler)


class Telnet_Client:
    def __init__(self, host=None, port=None):
        self.host = host
        self.port = port
        self.finish = b']# '
        # self.is_bootup = False
        self.masterctl = "datamasterctl"
        self.tn = Telnet(self.host, self.port)

    def login(self):
        if self.is_login():
            return True
        self.tn.write(b'\n')
        if b'login:' not in self.tn.read_until(b'login:', timeout=2):
            return False
        # print('login is in stdout')
        self.tn.write(b'root\n')
        if b'Password:' not in self.tn.read_until(b'Password:', timeout=2):
            return False
        # print('password is in stdout')
        self.tn.write(b'Huawei12#$\n')
        self.tn.read_until(self.finish, timeout=2)
        return self.is_login()

    def is_login(self):
        self.tn.write(b'\n')
        if b']# ' in self.tn.read_until(self.finish, timeout=2):
            return True
        return False

    def send_cmd(self, cmd, timeout=0.5, debug=False, flag=None, env=None):
        if env:
            cmd = 'source /etc/profile;export LD_PRELOAD=/lib64/libc.so.6;%s' % cmd
        if flag:
            cmd = 'ssh -o StrictHostKeyChecking=no root@192.168.2.76 "%s"' % cmd
        my_loger.info('----->send %s' % cmd)
        self.tn.write((cmd + '\n').encode())
        result = self.tn.read_until(self.finish, timeout=timeout).decode()
        if result and debug:
            my_loger.debug(result)
        return result

    def close(self):
        self.tn.close()

    def get_masterctl(self):
        time.sleep(1)
        result = self.send_cmd(r"which datamasterctl || which rosmasterctl",
                               debug=True)
        result = re.findall(r'/(datamasterctl|rosmasterctl)', result)
        if result:
            self.masterctl = result[0]

    def wating_mdc_bootup(self, keyword='iam service released: 0'):
        start_time = time.time()
        while time.time() - start_time < 500:
            try:
                result = self.tn.read_until(b'\n', timeout=2).decode()
                # sys.stdout.write(result)
                # sys.stdout.flush()
                my_loger.debug(result.rstrip())
                if keyword in result:
                    my_loger.info('-------->boot up success!')
                    break
            except Exception:
                pass
        time.sleep(1)
        return self.login()

    def wating_mdc_bootup_1(self, keyword='setting /run_id to'):
        hit_pot = False
        start_time = time.time()
        while time.time() - start_time < 500:
            try:
                result = self.tn.read_until(b'\n', timeout=2).decode()
                # sys.stdout.write(result)
                # sys.stdout.flush()
                my_loger.debug(result.rstrip())
                if 'Finish done.' in result:
                    hit_pot = True
                if keyword in result and hit_pot:
                    my_loger.info('-------->boot up success!')
                    break
            except Exception:
                pass
        time.sleep(1)
        return self.login()


def bytes_to_str(bytes_or_str):
    if isinstance(bytes_or_str, bytes):
        value = bytes_or_str.decode('utf-8')
    else:
        value = bytes_or_str
    return value


class SSH_Client:
    def __init__(self, hostname, username, password, port=22):
        self.host = hostname
        self.port = port
        self.username = username
        self.pwd = password
        self.client = paramiko.SSHClient()
        self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    def connect(self):
        self.client.connect(self.host,
                            port=self.port,
                            username=self.username,
                            password=self.pwd)

    def close(self):
        self.client.close()

    def run_cmd(self, cmd, timeout=0.5, env=None):
        if env:
            cmd = 'source /etc/profile;export LD_PRELOAD=/lib64/libc.so.6;' + cmd
        stdin, stdout, stderr = self.client.exec_command(cmd, timeout=timeout)
        return bytes_to_str(stdout.read()), bytes_to_str(stderr.read())

    def upload(self, local_path, target_path):
        sftp = self.client.open_sftp()
        sftp.put(local_path, target_path)
        # sftp.chmod(target_path, 0o755)

    def download(self, target_path, local_path):
        sftp = self.client.open_sftp()
        sftp.get(target_path, local_path)
