#!/usr/bin/env python3
import re
import os
import sys
import time
import argparse
import threading
from subprocess import run, PIPE, DEVNULL

current_dir = os.path.dirname(os.path.abspath(__file__))


def run_time(func):
    def wrapper(*args, **kwargs):
        print('Starting extracting apks,waiting...')
        start_time = time.time()
        func(*args, **kwargs)
        print('Finished with %.2f seconds' % (time.time() - start_time))
    return wrapper


def find_adb():
    if sys.platform == 'linux':
        proc = run(['which', 'adb'], stdout=PIPE)
        if proc.stdout:
            return 'adb'
        else:
            print("Can't find adb command,please install android-tools-adb")
            exit(1)

    elif sys.platform == 'win32':
        adb_path = os.path.join(current_dir, 'platform-tools', 'adb.exe')
        if os.path.isfile(adb_path):
            return adb_path
        else:
            print("please make sure platform-tools is in %s" % (current_dir))
            print("or use --adb argument to given adb binary")
            exit(1)
    else:
        print("This script only support linux and windows platform")
        exit(1)


def adb_command(command_list, shell=False, debug=None):
    '''运行adb命令，并返回进程，如果shell为真，则使用adb shell命令，debug=1
    则输出结果到标准输出，debug=2则输出结果到DEVNULL，默认为PIPE'''
    cmd_list = [adb]
    if shell:
        cmd_list.append('shell')
    cmd_list += command_list
    if debug == 1:
        stdout = sys.stdout
    elif debug == 2:
        stdout = DEVNULL
    else:
        stdout = PIPE
    proc = run(cmd_list, stdout=stdout,
               stderr=DEVNULL, universal_newlines=True)
    return proc


def list_apks(output_file=None):
    '''列出手机中所有已安装软件名称，如果output_file非空，则导出软件包名至文件中'''
    output = adb_command(['pm', 'list', 'packages'], shell=True).stdout
    apk_list = output.strip().split('\n')
    apk_names = []
    for apk_info in apk_list:
        apk_name = apk_info.replace('package:', '')
        apk_names.append(apk_name)
        apk_names.sort()
    if output_file:
        with open(output_file, 'w', newline='') as f:
            f.write(os.linesep.join(apk_names) + os.linesep)
    return apk_names


def search_apk(apk_name, apk_list):
    pattern = re.compile(apk_name, re.I)
    for apk in apk_list:
        if re.search(pattern, apk):
            print(apk)


def extract_apk(apk_name, extract_dir, apk_path=None):
    '''根据apk的名称与apk_path来提取软件包至extract_dir'''
    if not apk_path:
        output = adb_command(['pm', 'path', apk_name],
                             shell=True).stdout.strip()
        if output:
            apk_path = output.split('\n')[0].replace('package:', '')
        else:
            print("%s doesn't installed" % (apk_name))
            return
    proc = adb_command(['pull', apk_path, os.path.join(
        extract_dir, apk_name + '.apk')], debug=1)
    if proc.returncode == 0:
        with open(os.path.join(extract_dir, 'apk_list.txt'), 'a+', newline='') as f:
            f.write(apk_name + os.linesep)


@run_time
def parser_apks_tr(extract=None, thread_num=None):
    '''整理手机中已安装的软件包名，如果extract非空则提取对应软件包，默认最多5线程同时运行'''
    if not thread_num:
        thread_num = 6
    if extract == 'all' or extract == 'data':
        data_apk_dir = os.path.join(current_dir, 'data_apk')
        if not os.path.exists(data_apk_dir):
            os.makedirs(data_apk_dir)
        if os.path.exists(os.path.join(data_apk_dir, 'apk_list.txt')):
            os.remove(os.path.join(data_apk_dir, 'apk_list.txt'))
    if extract == 'all' or extract == 'system':
        system_apk_dir = os.path.join(current_dir, 'system_apk')
        if not os.path.exists(system_apk_dir):
            os.makedirs(system_apk_dir)
        if os.path.exists(os.path.join(system_apk_dir, 'apk_list.txt')):
            os.remove(os.path.join(system_apk_dir, 'apk_list.txt'))
    for apk_name in list_apks():
        output = adb_command(['pm', 'path', apk_name], shell=True).stdout
        apk_path = output.strip().split('\n')[0].replace('package:', '')
        if '/data/app/' in apk_path:
            if extract == 'all' or extract == 'data':
                t = threading.Thread(target=extract_apk, args=(
                    apk_name, data_apk_dir, apk_path), daemon=True)
                t.start()
        else:
            if extract == 'all' or extract == 'system':
                t = threading.Thread(target=extract_apk, args=(
                    apk_name, system_apk_dir, apk_path), daemon=True)
                t.start()
        while True:
            if len(threading.enumerate()) < thread_num:
                break
    while len(threading.enumerate()) > 1:
        pass


@run_time
def extract_apks_tr(apk_list, extract_dir, thread_num=None):
    '''根据apk_list来提取软件包至extract_dir，默认最多5线程同时运行'''
    if not thread_num:
        thread_num = 6
    if not os.path.exists(extract_dir):
        os.makedirs(extract_dir)
    if os.path.exists(os.path.join(extract_dir, 'apk_list.txt')):
        os.remove(os.path.join(extract_dir, 'apk_list.txt'))
    for apk_name in apk_list:
        apk_name = apk_name.strip()
        if apk_name:
            t = threading.Thread(target=extract_apk,
                                 args=(apk_name, extract_dir), daemon=True)
            t.start()
            while True:
                if len(threading.enumerate()) < thread_num:
                    break
    while len(threading.enumerate()) > 1:
        pass


def build_opt_parser():
    parser = argparse.ArgumentParser(
        '一个简单的脚本用于从手机中提取安装的软件包到指定目录中')
    parser.add_argument('--pull', action='store', nargs='+', metavar='apk_name',
                        help="提取一个或多个软件包到extract_apk目录")
    parser.add_argument('-l', '--list', action='store_true', default=False,
                        help="列出手机内已安装的所有系统软件包与用户软件包名称")
    parser.add_argument('-c', '--config', action='store', metavar='apk_list',
                        help="从文件中读取软件包名并提取软件包到extract_apk目录")
    parser.add_argument('--search', action='store', nargs='+', metavar='apk_name',
                        help="模糊查找一个或多个已安装的软件包名称,支持正则表达式")
    parser.add_argument('-o', '--output', action='store', metavar='apk_list',
                        help="导出所有已安装的系统软件包与用户软件包名称到文件中")
    parser.add_argument('--extract', action='store', choices=['all', 'data', 'system'],
                        help="选择需导出的软件包类型，所有已安装软件包或系统自带软件包或用户安装的软件包")
    parser.add_argument('-t', '--thread', action='store', type=int, metavar='thread_num',
                        help="设置最多允许同时运行的线程的个数，默认为5个线程")
    parser.add_argument('-e', '--adb', metavar='COMMAND', type=str,
                        help='使用该选项手动指定adb可执行路径.')
    return parser


def main():
    parser = build_opt_parser()
    options = parser.parse_args()
    basename = os.path.basename(__file__)
    extract_apk_dir = os.path.join(current_dir, 'extract_apk')
    global adb
    if options.adb:
        adb = options.adb
    else:
        adb = find_adb()
    if options.thread:
        thread_num = options.thread + 1
    else:
        thread_num = None
    if options.list:
        apk_list = list_apks()
        print(os.linesep.join(apk_list))
        exit(0)
    elif options.output:
        list_apks(output_file=options.output)
        exit(0)
    elif options.search:
        apk_list = list_apks()
        for apk_name in options.search:
            search_apk(apk_name, apk_list)
        exit(0)
    elif options.pull:
        extract_apks_tr(options.pull, extract_apk_dir, thread_num=thread_num)
        exit(0)
    elif options.extract:
        try:
            parser_apks_tr(extract=options.extract, thread_num=thread_num)
            exit(0)
        except KeyboardInterrupt:
            print("\n(^C) Control-C Interrupted")
            exit(1)
    elif options.config:
        with open(options.config) as f:
            apk_list = f.readlines()
        try:
            extract_apks_tr(apk_list, extract_apk_dir, thread_num=thread_num)
            exit(0)
        except KeyboardInterrupt:
            print("\n(^C) Control-C Interrupted")
            exit(1)
    else:
        parser.print_help()
        print('\nexample: ' + basename + ' --search apk_name1 apk_name2')
        print('         ' + basename + ' --pull apk_name1 apk_name2')
        print('         ' + basename + ' --config apk_list')
        print('         ' + basename + ' --extract data')


if __name__ == '__main__':
    main()
