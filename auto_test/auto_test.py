import sys
import time
import serial
import logging
from colorama import init
from pathlib import Path

# Console colors
init()
W = '\033[0m'  # white (normal)
R = '\033[31m'  # red
G = '\033[32m'  # green
O = '\033[33m'  # orange
B = '\033[34m'  # blue
P = '\033[35m'  # purple
C = '\033[36m'  # cyan
GR = '\033[37m'  # gray

PASS = '''
######   #####   #####   #####
 ##  ## ##   ## ##   ## ##   ##
 ##  ## ##   ## ##      ##
 #####  #######  #####   #####
 ##     ##   ##      ##      ##
 ##     ##   ## ##   ## ##   ##
####    ##   ##  #####   #####
'''
FAIL = '''
#######  #####  ###### ####
 ##  ## ##   ##   ##    ##
 ##     ##   ##   ##    ##
 ####   #######   ##    ##
 ##     ##   ##   ##    ##
 ##     ##   ##   ##    ##  ##
####    ##   ## ######  ######
'''

comport = 'com6'
date_format = "%H:%M:%S"
data_format = "[%(asctime)s]:%(message)s"


def handler(filename=None, filemode='a', backup=False,
            stream=None, msg_fmt=None, date_fmt=None):
    if filename:
        if backup:
            from logging.handlers import RotatingFileHandler
            handler = RotatingFileHandler(
                filename, maxBytes=1024000, backupCount=3)
        else:
            handler = logging.FileHandler(filename, mode=filemode)
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


def sendcommand(cmd, timeout=0.5):
    ser.write((cmd + '\r\n').encode())
    time.sleep(timeout)
    out = ser.readall()
    if out:
        out = out.decode().rstrip('\r\n')
        mylogger.debug(out)
    else:
        out = ""
    return out


def enter_mfg():
    start_time = time.time()
    while time.time() - start_time <= 30:
        ser.write(b'\r\n')
        out = ser.readline()
        if out:
            try:
                mylogger.debug(out.decode().rstrip('\r\n'))
            except Exception as e:
                print(e)
        if b'Tegra124 (Jetson TK1)' in out:
            return True
    return False


def set_mfg_on():
    ser.reset_input_buffer()
    ser.reset_output_buffer()
    sendcommand('setenv mfg_mode on')
    sendcommand("setenv bootpart '2'")
    sendcommand('saveenv')
    sendcommand('boot')


def boot_up():
    start_time = time.time()
    while time.time() - start_time <= 120:
        out = ser.readline()
        if out:
            try:
                mylogger.debug(out.decode().rstrip('\r\n'))
            except Exception as e:
                print(e)
        # if b'Board: NVIDIA Jetson TK1' in out:
        #     print("")
        #     print('Enter mfg_mode on success')
        #     return True
        if b'root@tegra-ubuntu' in out:
            print("")
            print('Enter test mode success')
            return True
        elif b'root@EEDII-for-Conf-Room' in out:
            print("")
            print('Enter test mode fail')
            return False
    return False


def copy_files():
    ser.reset_input_buffer()
    ser.reset_output_buffer()
    out = sendcommand('mount /dev/sda1 /mnt;$?', timeout=1)
    if 'bash: 0' not in out:
        print('Mount usb device fail')
        return False
    out = sendcommand(
        'cp /mnt/upload1.sh /root/scripts/test_scripts/;$?', timeout=1)
    if 'bash: 0' not in out:
        print('Copy files fail')
        return False
    out = sendcommand(
        'cp /mnt/manfcert /system/bin;$?', timeout=1)
    if 'bash: 0' not in out:
        print('Copy files fail')
        return False
    print('Copy files success')
    return True

if __name__ == '__main__':
    try:
        ser = serial.Serial(comport, 115200, timeout=0.5)
    except Exception as e:
        sys.exit(f'Open port {O}{comport}{W} fail')
    else:
        if ser.is_open:
            print(f'Open port {O}{comport}{W} success')

    try:
        SN = input('请输入SN并按回车确认：')
        date = time.strftime('%Y%m%d%H%M%S', time.localtime())
        file_name = SN + '_' + date + '.log'
        log_dir = Path('Log')
        log_dir.mkdir(exist_ok=True)
        log_dir = Path(log_dir, date[0:6])
        log_dir.mkdir(exist_ok=True)
        log_path = Path(log_dir, file_name)
        uart_handler = handler(filename=str(log_path), filemode='w',
                               msg_fmt=data_format, date_fmt=date_format)
        std_handler = handler()
        mylogger = logger(name=__name__, handler=std_handler)
        mylogger.addHandler(uart_handler)
        if enter_mfg():
            set_mfg_on()
            if boot_up() and copy_files():
                print(f'{G}{PASS}{W}')
            else:
                print(f'{R}{FAIL}{W}')
        else:
            print('Enter mfg_mode on fail')
            print(f'{R}{FAIL}{W}')
    except KeyboardInterrupt:
        pass
    except Exception as e:
        print(e)
    finally:
        ser.reset_input_buffer()
        ser.reset_output_buffer()
        ser.flush()
        ser.close()
