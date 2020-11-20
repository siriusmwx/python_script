import os
import sys
import csv
import time
import socket
import threading
from subprocess import run


def get_host_ip():
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
        sock.connect(('172.24.255.212', 80))
        ip = sock.getsockname()[0]
    return ip


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
        # self.name = host_name
        self.user = ""
        self.passwd = ""
        self.status = ""


def host_status(host_ip):
    proc = run(['ping', host_ip, '-n', '2'],
               capture_output=True, universal_newlines=True)
    if 'TTL=' in proc.stdout:
        active_ips.add(host_ip)
        print("%s is online" % host_ip)


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


def magic_wakeon(host):
    if not host.status:
        # proc = run('mc-wol %s' % host.mac, capture_output=True)
        send_magic_packet(host.mac, port=8384)
        print('Send magic packet to %s<==>%s' % (host.ip, host.mac))
        return True
    print("The host %s<==>%s is already power on" % (host.ip, host.mac))


def remote_shutdown(host):
    if host.status:
        if host.user and host.passwd:
            proc = run('net use \\\\%s %s /user:%s' % (
                host.ip, host.passwd, host.user), capture_output=True)
            if proc.returncode != 0:
                print('Fail to power off %s<==>%s' % (host.ip, host.mac))
                return
            proc = run('shutdown /m \\\\%s /s /f /t 0' %
                       host.ip, capture_output=True)
            if proc.returncode != 0:
                print('Fail to power off %s<==>%s' % (host.ip, host.mac))
                return
            print('Success to power off %s<==>%s' % (host.ip, host.mac))
            return True
    else:
        print("The host %s<==>%s is already power off" % (host.ip, host.mac))


def update_hosts():
    print('Starting update hosts from csv file')
    hosts = {}
    if os.path.exists('hosts.csv'):
        with open('hosts.csv') as f:
            csv_reader = csv.DictReader(f)
            for host in csv_reader:
                hosts[host['MAC']] = Host(host['MAC'], host['IP'])
                hosts[host['MAC']].user = host['USER']
                hosts[host['MAC']].passwd = host['PASSWORD']

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
            hosts[host_mac].status = "ON"
    host_list = list(hosts.values())
    host_list.sort(key=lambda x: int(x.ip.split('.')[-1]))
    return host_list


def remote_hosts(hosts, action=None):
    if action == 'on':
        print('Starting remote hosts to power on')
        for host in hosts:
            magic_wakeon(host)
    else:
        print('Starting remote hosts to power off')
        for host in hosts:
            remote_shutdown(host)


def update_csv(host_list):
    print('Starting update hosts to csv file')
    with open('hosts.csv', 'w', newline='') as f:
        csv_writer = csv.DictWriter(
            f, fieldnames=['IP', 'MAC', 'USER', 'PASSWORD', 'STATUS'])
        csv_writer.writeheader()
        for host in host_list:
            csv_writer.writerow({
                'MAC': host.mac,
                'IP': host.ip,
                'USER': host.user,
                'PASSWORD': host.passwd,
                'STATUS': host.status
            })


if __name__ == '__main__':
    active_ips = set()
    ip_header = ('.').join(get_host_ip().split('.')[0:3])
    ip_list = ['%s.%s' % (ip_header, x) for x in range(1, 255)]
    try:
        ping_ips()
        hosts = update_hosts()
        update_csv(hosts)
        if len(sys.argv) == 2:
            remote_hosts(hosts, action=sys.argv[1])
        else:
            sys.exit("args must be 'on' or 'off'")
    except KeyboardInterrupt:
        sys.exit()
    except Exception as e:
        sys.exit(e)
