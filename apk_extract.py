#!/usr/bin/env python3
import re
import os
import sys
import argparse
from subprocess import run, PIPE, DEVNULL


def find_adb():
    global adb
    if sys.platform == 'linux':
        proc = run(['which', 'adb'], stdout=PIPE)
        if proc.stdout:
            adb = 'adb'
        else:
            print("Can't find adb command,please install android-tools-adb")
            exit(1)

    elif sys.platform == 'win32':
        adb_path = os.path.join(current_dir, 'platform-tools', 'adb.exe')
        if os.path.isfile(adb_path):
            adb = adb_path
        else:
            print("please make sure platform-tools is in %s" % (current_dir))
            exit(1)
    else:
        print("This script only support linux and windows platform")
        exit(1)


def adb_command(cmd, shell=False, debug=None):
    '''运行adb命令，并返回进程的输出，如果shell为真，则使用adb shell命令，
    debug=1则输出结果到标准输出，debug=2则输出结果到devnull'''
    cmd_list = [adb]
    if shell:
        cmd_list.append('shell')
    cmd_list += cmd.strip().split()
    if debug == 1:
        stdout = sys.stdout
    elif debug == 2:
        stdout = DEVNULL
    else:
        stdout = PIPE
    proc = run(cmd_list, stdout=stdout,
               stderr=DEVNULL, universal_newlines=True)
    return proc.stdout


def list_apks(output_file=None):
    '''列出手机中所有已安装软件名称，如果output_file有值，则导出软件包名至文件中'''
    output = adb_command('pm list packages', shell=True)
    apk_list = output.strip().split('\n')
    apk_names = []
    for apk_info in apk_list:
        apk_name = apk_info.replace('package:', '')
        apk_names.append(apk_name)
        apk_names.sort()
    if output_file:
        with open(output_file, 'w') as f:
            f.write(os.linesep.join(apk_names) + os.linesep)
    return apk_names


def parser_apks(extract=None):
    '''整理手机中已安装的软件包名并返回系统与用户软件包列表，如果extract非空则提取对应软件包'''
    output = adb_command('pm list packages', shell=True)
    apk_list = output.strip().split('\n')
    system_apk_list = []
    data_apk_list = []
    if extract:
        data_apk_txt = os.path.join(data_apk_dir, 'apk_list.txt')
        system_apk_txt = os.path.join(system_apk_dir, 'apk_list.txt')
        data_writer = open(data_apk_txt, 'w')
        system_writer = open(system_apk_txt, 'w')
        data_writer.close()
        system_writer.close()
    for apk_info in apk_list:
        apk_name = apk_info.replace('package:', '')
        output = adb_command('pm path ' + apk_name, shell=True)
        apk_path = output.strip().split('\n')[0].replace('package:', '')
        if '/data/app/' in apk_path:
            data_apk_list.append(apk_name)
            if extract == 'all' or extract == 'data':
                adb_command('pull ' + apk_path + ' ' +
                            os.path.join(data_apk_dir, apk_name + '.apk'), debug=1)
                with open(data_apk_txt, 'a+') as f:
                    f.write(apk_name + os.linesep)
        else:
            system_apk_list.append(apk_name)
            if extract == 'all' or extract == 'system':
                adb_command('pull ' + apk_path + ' ' +
                            os.path.join(system_apk_dir, apk_name + '.apk'), debug=1)
                with open(system_apk_txt, 'a+') as f:
                    f.write(apk_name + os.linesep)
    return data_apk_list, system_apk_list


def extract_apk(apk_name):
    '''根据apk的名称提取软件包到extract_apk文件夹下'''
    output = adb_command('pm path ' + apk_name, shell=True).strip()
    if output:
        apk_path = output.split('\n')[0].replace('package:', '')
        adb_command('pull ' + apk_path + ' ' +
                    os.path.join(extract_apk_dir, apk_name + '.apk'), debug=1)
    else:
        print("%s doesn't installed" % (apk_name))


def search_apk(apk_name, apk_list):
    pattern = re.compile(apk_name, re.I)
    for apk in apk_list:
        if re.search(pattern, apk):
            print(apk)


def build_opt_parser():
    parser = argparse.ArgumentParser(description='一个简单的脚本用于从手机中提取安装的软件包到指定目录中')
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
    return parser


def main():
    parser = build_opt_parser()
    options = parser.parse_args()
    find_adb()
    if not os.path.exists(data_apk_dir):
        os.makedirs(data_apk_dir)
    if not os.path.exists(system_apk_dir):
        os.makedirs(system_apk_dir)
    if not os.path.exists(extract_apk_dir):
        os.makedirs(extract_apk_dir)
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
        for apk_name in options.pull:
            extract_apk(apk_name)
        exit(0)
    elif options.extract:
        try:
            parser_apks(extract=options.extract)
            exit(0)
        except KeyboardInterrupt:
            print("\n(^C) Control-C interrupted")
            exit(1)
    elif options.config:
        with open(options.config) as f:
            for apk_name in f:
                apk_name = apk_name.strip()
                if apk_name:
                    extract_apk(apk_name)
        exit(0)
    else:
        parser.print_help()
        print('\nexample: ' + basename + ' --search apk_name1 apk_name2')
        print('         ' + basename + ' --pull apk_name1 apk_name2')
        print('         ' + basename + ' --config apk_list')
        print('         ' + basename + ' --extract data')


if __name__ == '__main__':
    current_dir = os.path.dirname(os.path.abspath(__file__))
    basename = os.path.basename(__file__)
    data_apk_dir = os.path.join(current_dir, 'data_apk')
    system_apk_dir = os.path.join(current_dir, 'system_apk')
    extract_apk_dir = os.path.join(current_dir, 'extract_apk')
    main()
