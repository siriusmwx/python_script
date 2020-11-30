import os
import sys
import re
import csv
import time
import socket
import threading
import argparse
from subprocess import run

# Console colors
W = '\033[0m'  # white (normal)
R = '\033[31m'  # red
G = '\033[32m'  # green
O = '\033[33m'  # orange
B = '\033[34m'  # blue
P = '\033[35m'  # purple
C = '\033[36m'  # cyan
GR = '\033[37m'  # gray


def get_host_ip():
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
        sock.connect(('172.24.255.212', 80))
        ip = sock.getsockname()[0]
    print(f'Your host IP is {O}{ip}{W}')
    return ip


def host_status(host_ip):
    proc = run(['ping', host_ip, '-n', '2'],
               capture_output=True, universal_newlines=True)
    if 'TTL=' in proc.stdout:
        active_ips.add(host_ip)
        print(f"{G}{host_ip}{W} is {O}online{W}")


def ping_ips():
    start_time = time.time()
    for ip in ip_list:
        t = threading.Thread(target=host_status, args=(ip,), daemon=True)
        t.start()
        # while True:
        #     if len(threading.enumerate()) < 50:
        #         break
    while len(threading.enumerate()) > 1 and time.time() - start_time <= 60:
        pass


def create_magic_packet(macaddress):
    """
    Create a magic packet.

    A magic packet is a packet that can be used with the for wake on lan
    protocol to wake up a computer. The packet is constructed from the
    mac address given as a parameter.

    Args:
        macaddress (str): the mac address that should be parsed into a
            magic packet.

    """
    if len(macaddress) == 17:
        sep = macaddress[2]
        macaddress = macaddress.replace(sep, "")
    elif len(macaddress) != 12:
        raise ValueError("Incorrect MAC address format")

    return bytes.fromhex("F" * 12 + macaddress * 16)


def send_magic_packet(*macs, **kwargs):
    """
    Wake up computers having any of the given mac addresses.

    Wake on lan must be enabled on the host device.

    Args:
        macs (str): One or more macaddresses of machines to wake.

    Keyword Args:
        ip_address (str): the ip address of the host to send the magic packet
                     to (default "255.255.255.255")
        port (int): the port of the host to send the magic packet to
               (default 9)

    """
    ip = kwargs.pop("ip_address", "255.255.255.255")
    port = kwargs.pop("port", 9)
    for k in kwargs:
        raise TypeError(
            "send_magic_packet() got an unexpected keyword " "argument {!r}".format(
                k)
        )

    packets = [create_magic_packet(mac) for mac in macs]

    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        sock.connect((ip, port))
        for packet in packets:
            sock.send(packet)


class Host():

    def __init__(self, host_mac, host_ip):
        self.mac = host_mac
        self.ip = host_ip
        self.user = ""
        self.passwd = ""
        self.status = ""
        self.model = ""

    def remote_host(self, action=None, model=None):
        if model:
            if not model.search(self.model):
                return
        if action:
            # print(f'Starting remote hosts to {O}power on{W}')
            self.magic_wakeon()
        else:
            # print(f'Starting remote hosts to {O}power off{W}')
            self.remote_shutdown()

    def magic_wakeon(self):
        if self.ip not in active_ips:
            self.status = 'OFF'
            # proc = run('mc-wol %s' % self.mac, capture_output=True)
            send_magic_packet(self.mac, port=8384)
            print(f'Send magic packet to {G}{self.ip}{W}<==>{O}{self.mac}{W}')
            return True
        self.status = 'ON'
        print(f"The host {G}{self.ip}{W}<==>{O}{self.mac}{W} is already {C}power on{W}")

    def remote_shutdown(self):
        if self.ip in active_ips:
            self.status = 'ON'
            if self.user and self.passwd:
                proc = run('net use \\\\%s %s /user:%s' % (
                    self.ip, self.passwd, self.user), capture_output=True)
                if proc.returncode != 0:
                    print(f'{R}Fail{W} to remote host {G}{self.ip}{W}<==>{O}{self.mac}{W}')
                    return
                proc = run('shutdown /m \\\\%s /s /f /t 0' %
                           self.ip, capture_output=True)
                if proc.returncode != 0:
                    print(f'{R}Fail{W} to power off {G}{self.ip}{W}<==>{O}{self.mac}{W}')
                    return
                print(f'{G}Success{W} to power off {G}{self.ip}{W}<==>{O}{self.mac}{W}')
                self.status = 'OFF'
                return True
        else:
            self.status = 'OFF'
            print(f"The host {G}{self.ip}{W}<==>{O}{self.mac}{W} is already {C}power off{W}")


def update_hosts():
    hosts = {}
    if os.path.exists(csv_file):
        print(f'Starting update hosts from {O}{csv_file}{W} file')
        with open(csv_file) as f:
            csv_reader = csv.DictReader(f)
            for host in csv_reader:
                hosts[host['MAC']] = Host(host['MAC'], host['IP'])
                hosts[host['MAC']].user = host['USER']
                hosts[host['MAC']].passwd = host['PASSWORD']
                hosts[host['MAC']].model = host['MODEL']

    proc = run(['arp', '-a'], capture_output=True, universal_newlines=True)
    for result in proc.stdout.split('\n'):
        result = result.split()
        if result and result[0] in active_ips:
            host_mac = result[1].replace('-', ':')
            host_ip = result[0]
            if host_mac not in hosts:
                hosts[host_mac] = Host(host_mac, host_ip)
            else:
                hosts[host_mac].mac = host_mac
                hosts[host_mac].ip = host_ip
    host_list = list(hosts.values())
    host_list.sort(key=lambda x: int(x.ip.split('.')[-1]))
    return host_list


def update_csv(host_list):
    print(f'Starting update hosts to {O}{csv_file}{W} file')
    with open(csv_file, 'w', newline='') as f:
        csv_writer = csv.DictWriter(
            f, fieldnames=['IP', 'MAC', 'USER', 'PASSWORD', 'STATUS', 'MODEL'])
        csv_writer.writeheader()
        for host in host_list:
            csv_writer.writerow({
                'MAC': host.mac,
                'IP': host.ip,
                'USER': host.user,
                'PASSWORD': host.passwd,
                'STATUS': host.status,
                'MODEL': host.model
            })


def arg_parser():
    parser = argparse.ArgumentParser(
        description='a simple script use to remote hosts to power on or off')
    group1 = parser.add_mutually_exclusive_group()
    group1.add_argument('-on', '--on', action='store_true',
                        help='使用此选项用于远程启动计算机')
    group1.add_argument('-off', '--off', action='store_true',
                        help='使用此选项用于远程关闭计算机')
    parser.add_argument('--model', action='store', nargs='+',
                        help='指定需要执行远程启动或关闭的机种，可为多个机种')
    parser.add_argument(
        "--mac",
        metavar="MAC",
        nargs="+",
        help="The mac addresses or of the computers you are trying to wake."
    )
    parser.add_argument(
        "-i",
        metavar="ip",
        default="255.255.255.255",
        help="The ip address of the host to send the magic packet to "
        "(default 255.255.255.255)."
    )
    parser.add_argument(
        "-p",
        metavar="port",
        type=int,
        default=9,
        help="The port of the host to send the magic packet to "
        "(default 9)."
    )
    return parser


if __name__ == '__main__':
    parser = arg_parser()
    args = parser.parse_args()
    os.system('cls')
    active_ips = set()
    ip_header = ('.').join(get_host_ip().split('.')[0:3])
    csv_file = ip_header.replace('.', '_') + '.csv'
    ip_list = ['%s.%s' % (ip_header, x) for x in range(1, 255)]
    try:
        ping_ips()
        hosts = update_hosts()
        model = ""
        if args.on:
            if args.model:
                print(f"The select model is {O}{' '.join(args.model)}{W}")
                model = re.compile('|'.join(args.model), re.I)
            print(f'Starting remote hosts to {O}power on{W}')
            for host in hosts:
                host.remote_host(action=True, model=model)
        elif args.off:
            if args.model:
                print(f"The select model is {O}{' '.join(args.model)}{W}")
                model = re.compile('|'.join(args.model), re.I)
            print(f'Starting remote hosts to {O}power off{W}')
            for host in hosts:
                host.remote_host(model=model)
        elif args.mac:
            send_magic_packet(
                *args.mac, ip_address=args.i, port=args.p)
        update_csv(hosts)
    except KeyboardInterrupt:
        sys.exit()
    except Exception as e:
        sys.exit(e)
