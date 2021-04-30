# -*- coding:utf-8 -*-
import os
import sys
import time
from telnetlib import Telnet
from subprocess import Popen, PIPE

def AsciiStr2CharStr(asciiStr):
    charStr = ''
    if len(asciiStr) % 2 != 0:
        return charStr
    for i in range(0, len(asciiStr) / 2):
        charStr += chr(int(asciiStr[2 * i:2 * i + 2], 16))
    return charStr


def wating_mdc_connect():
    status = False
    start_time = time.time()
    proc = Popen('ping 10.246.55.38 -t',
                 stdout=PIPE,
                 stderr=PIPE,
                 universal_newlines=True)
    try:
        while time.time() - start_time < 300:
            stdout = proc.stdout.readline()
            sys.stdout.write(stdout)
            if 'TTL=' in stdout:
                status = True
                break
    finally:
        proc.kill()
    return status


class Telnet_Client:
    def __init__(self, host=None, port=None):
        self.host = host
        self.port = port
        self.finish = ']# '
        self.is_bootup = False
        self.tn = Telnet(self.host, self.port)

    def login(self):
        if self.is_login():
            return True
        self.tn.write('\n')
        if 'login:' not in self.tn.read_until('login:', timeout=2):
            return False
        # print('login is in stdout')
        self.tn.write('root\n')
        if 'Password:' not in self.tn.read_until('Password:', timeout=2):
            return False
        # print('password is in stdout')
        self.tn.write('Huawei12#$\n')
        self.tn.read_until(self.finish, timeout=2)
        return self.is_login()

    def is_login(self):
        self.tn.write('\n')
        if ']# ' in self.tn.read_until(self.finish, timeout=2):
            if not self.is_bootup:
                self.is_bootup = True
            return True
        return False

    def send_cmd(self, cmd, timeout=0.5):
        print('----->send %s' % cmd)
        self.tn.write(cmd + '\n')
        return (self.tn.read_until(self.finish, timeout=timeout))

    def close(self):
        self.tn.close()

    def wating_mdc_bootup(self, keyword='iam service released: 0'):
        # if self.login():
        #     return True
        start_time = time.time()
        while time.time() - start_time < 500:
            try:
                result = self.tn.read_until('\n', timeout=2)
                sys.stdout.write(result)
                sys.stdout.flush()
                if keyword in result:
                    print('-------->boot up success!')
                    break
            except Exception:
                pass
        time.sleep(1)
        return self.login()

    def start_diag_server(self):
        self.send_cmd('ifconfig ethd0 10.246.55.38 netmask 255.255.255.0')
        time.sleep(1)
        self.send_cmd('route add default gw 10.246.55.1')
        time.sleep(1)
        result = self.send_cmd('netstat -anp | grep 13400', timeout=1)
        if '10.246.55.38' in result:
            return True
        self.send_cmd(
            "sed -i 's#192.168.69.41#10.246.55.38#1g' /etc/ads/service/mdc_conf/dm_config.json"
        )
        time.sleep(1)
        count = 0
        while count <= 5:
            self.send_cmd(
                'pmupload rosmasterctl restart diag_server /etc/ads/service/mdc_conf/dm_config.json'
            )
            count += 1
            time.sleep(5)
            result = self.send_cmd('netstat -anp | grep 13400', timeout=1)
            print(result)
            if '10.246.55.38' in result:
                return True
        return False

def main():
    mdc_client = Telnet_Client(host='10.246.55.45', port=10005)
    try:
        if not mdc_client.login():
            if not mdc_client.wating_mdc_bootup():
                sys.exit('login mdc fail')
        time.sleep(1)
        if not mdc_client.start_diag_server():
            print('start reboot mdc and try again,wating...')
            mdc_client.send_cmd('reboot\n')
            if not mdc_client.wating_mdc_bootup():
                sys.exit('login mdc fail')
            time.sleep(1)
            if not mdc_client.start_diag_server():
                sys.exit('start diag_server fail!')
        print('start diag_server success!')
        print('start wating mdc connect!')
        if not wating_mdc_connect():
            sys.exit('connect to mdc fail!')
        print('connect to mdc success,wating 5s to start upgrade!')
        time.sleep(5)
        local_upgrade()
        mdc_client.wating_mdc_bootup(keyword='Finish done')
    except KeyboardInterrupt:
        sys.exit('KeyboardInterrupt Ctr-C')
    # except Exception, e:
    #     sys.exit(e)
    finally:
        mdc_client.close()


if __name__ == '__main__':
    main()
