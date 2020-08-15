import os
import time
import logging
import threading
from subprocess import Popen, PIPE, DEVNULL

data_format = "%a %d %b %Y %H:%M:%S"
msg_format = "%(asctime)s::%(name)s::%(levelname)s::%(threadName)s::%(message)s"
std_format = "%(asctime)s:%(name)s:%(levelname)s:%(message)s"


class clean_device(threading.Thread):

    def __init__(self, name=None, device=None, daemon=None):
        super().__init__(name=name, daemon=daemon)
        self.device = device

    def run(self):
        std_logger.debug('Start to clean %s' % (self.device))
        proc = Popen('DeviceCleanupCmd "%s" -t' % (self.device),
                     stdout=PIPE, stderr=DEVNULL, shell=True, universal_newlines=True)
        while proc.poll() == None:
            my_loger.info(proc.stdout.readline().rstrip())
        if proc.returncode == 0:
            std_logger.debug('Success to clean %s' % (self.device))


def run_time(func):
    def wrapper(*args, **kwargs):
        std_logger.debug('Start to clean devices,please waiting...')
        start_time = time.time()
        func(*args, **kwargs)
        std_logger.debug('Finished clean with %.2f seconds' %
                         (time.time() - start_time))
    return wrapper


@run_time
def clean_tr(device_list, thread_num=None):
    if not thread_num:
        thread_num = 6
    for device in device_list:
        task = clean_device(device=device.rstrip(), daemon=True)
        task.start()
        while True:
            if len(threading.enumerate()) < thread_num:
                break
    while len(threading.enumerate()) > 1:
        pass


def handler(filename=None,  filemode='a', backup=False,
            stream=None, msg_fmt=None, data_fmt=None):
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
        formatter = logging.Formatter(fmt=msg_fmt, datefmt=data_fmt)
        handler.setFormatter(formatter)
    return handler


def logger(name=None, handler=None, level=logging.DEBUG):
    logger = logging.getLogger(name)
    logger.setLevel(level)
    if handler:
        logger.addHandler(handler)
    return logger

if __name__ == '__main__':
    file_handler = handler('clean.log', backup=True, msg_fmt=msg_format)
    std_handler = handler(msg_fmt=std_format, data_fmt=data_format)
    my_loger = logger(name='cleanup', handler=file_handler)
    std_logger = logger(name='stdout', handler=std_handler)
    std_logger.addHandler(file_handler)
    current_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(current_dir)
    with open('device.txt') as f:
        device_list = f.readlines()
    try:
        clean_tr(device_list)
    except KeyboardInterrupt:
        print("\n(^C) Control-C Interrupt")
        exit(1)
