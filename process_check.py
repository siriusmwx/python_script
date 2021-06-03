# -*- coding:utf-8 -*-
# from __future__ import print_function
import os
import re
import sys
import time
import yaml
import paramiko

currend_dir = os.path.dirname(os.path.abspath(__file__))
os.chdir(currend_dir)
state_dic = {
    "1,3": ["SS_MPI_APP_LIST", "SS_OM_APP_LIST", "SS_BASIC_SRV_APP_LIST"],
    "1,4": ["SS_AVP_APP_LIST", "SS_OM_APP_LIST", "SS_BASIC_SRV_APP_LIST"],
    "3,5": "SS_INSTALL_APP_LIST",
    "3,6": "SS_VERIFY_APP_LIST",
    "4,0": "SS_CAL_APP_LIST"
}
vehicle = {}


def bytes_to_str(bytes_or_str):
    if isinstance(bytes_or_str, bytes):
        value = bytes_or_str.decode('utf-8')
    else:
        value = bytes_or_str
    return value


class MDC_SSH_Client:
    def __init__(self, hostname, username, password, port=22):
        self.host = hostname
        self.port = port
        self.username = username
        self.pwd = password
        self.vehicle_info = {}
        self.board_type = ""
        self.client = paramiko.SSHClient()
        self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    def connect(self):
        self.client.connect(self.host,
                            port=self.port,
                            username=self.username,
                            password=self.pwd)

    def get_board_type(self):
        stdout, stderr = self.run_cmd(
            r"ifconfig ethx0 | grep -q '192.168.2.12' && echo 'A'")
        self.board_type = stdout.strip()
        if self.board_type:
            return True
        stdout, stderr = self.run_cmd(
            r"ifconfig ethx0 | grep -q '192.168.2.76' && echo 'B'")
        self.board_type = stdout.strip()
        return self.board_type

    def close(self):
        self.client.close()

    def run_cmd(self, cmd, timeout=0.5, env=None):
        if env:
            cmd = 'source /etc/profile;' + cmd
        stdin, stdout, stderr = self.client.exec_command(cmd, timeout=timeout)
        return bytes_to_str(stdout.read()), bytes_to_str(stderr.read())

    def upload(self, local_path, target_path):
        sftp = self.client.open_sftp()
        sftp.put(local_path, target_path)
        # sftp.chmod(target_path, 0o755)

    def download(self, target_path, local_path):
        sftp = self.client.open_sftp()
        sftp.get(target_path, local_path)

    def get_vehicle_info(self):
        stdout, stderr = self.run_cmd('rosparam get cfgmgr_env', timeout=5)
        for item in stdout.strip().split('\n'):
            info = item.split(':')
            self.vehicle_info[info[0]] = info[1].strip()

    def get_app_launch_total(self):
        yaml_files = []
        app_launch_file = os.path.join(self.board_type, 'app_launch.yaml')
        app_launch_total_file = os.path.join(self.board_type,
                                             'app_launch_total.yaml')
        self.download('/etc/ads/service/ss/app_launch.yaml', app_launch_file)
        with open(app_launch_file) as f:
            app_launch_config = yaml.load(f)
        for path in app_launch_config['startup_path_list']:
            if r"${vehicle_factory}" in path:
                path = path.replace(
                    r"${vehicle_factory}",
                    self.vehicle_info['vehicle_factory']).replace(
                        r'${vehicle_type}', self.vehicle_info['vehicle_type'])
            local_path = os.path.join(self.board_type, path.split('/')[-1])
            yaml_files.append(local_path)
            self.download(path, local_path)
        with open(app_launch_total_file, 'w') as f:
            for file in yaml_files:
                with open(file) as f1:
                    yaml.dump(yaml.load(f1), f)

    def parse_processes(self, full_process_names):
        pattern = re.compile('[0-9]{2}:[0-9]{2}:[0-9]{2} ')
        process_dict = {x: [] for x in full_process_names}
        for i in range(3):
            stdout, stderr = self.run_cmd('ps -elf', timeout=2, env=True)
            process_list = stdout.strip().split('\n')
            for process_info in process_list:
                process_pid = process_info.split()[3]
                process_name = pattern.split(process_info)[-1]
                if process_name in process_dict:
                    process_dict[process_name].append(process_pid)
            time.sleep(5)
        return process_dict


def main(ip, user, passwd):
    client = MDC_SSH_Client(ip, user, passwd)
    try:
        client.connect()
        client.get_vehicle_info()
        if not client.vehicle_info:
            print('get vehicle_info fail')
            return
        print('The vehicle_info is %s' % client.vehicle_info)
        client.get_board_type()
        if not client.board_type:
            print('get board_type fail')
            return
        print('The board type is %s' % client.board_type)
        if not os.path.exists(client.board_type):
            os.mkdir(client.board_type)
        mdc_base_app_file = os.path.join(
            client.board_type, 'mdc_base_app_%s.yaml' % client.board_type)
        app_launch_file = os.path.join(client.board_type, 'app_launch.yaml')
        app_launch_total_file = os.path.join(client.board_type,
                                             'app_launch_total.yaml')
        stdout, stderr = client.run_cmd(r"pmupload mdc_ss_dfx query-state",
                                        timeout=5,
                                        env=True)
        state = re.search(' ([0-9],[0-9]+)', stdout).group(1)
        if state not in state_dic:
            print('%s not in state_dic' % state)
            return
        client.download(
            '/etc/ads/service/ss/mdc_base_app_%s.yaml' % client.board_type,
            mdc_base_app_file)
        client.download('/etc/ads/service/ss/app_launch.yaml', app_launch_file)
        with open(mdc_base_app_file) as f:
            mdc_base_app_config = yaml.load(f)
        client.get_app_launch_total()
        with open(app_launch_total_file) as f:
            app_launch_config = yaml.load(f)
        full_process_names = set()
        for app_list in state_dic[state]:
            print(app_list)
            try:
                for key in mdc_base_app_config[app_list]:
                    if mdc_base_app_config[app_list][key]["OptionType"] != 0:
                        continue
                    # print "%s stage :check app %s".format(app_list, key)
                    if not mdc_base_app_config[app_list][key]["Arguments"]:
                        full_process_name = app_launch_config[key]["bin_path"]
                        full_process_names.add(full_process_name)
                    else:
                        full_process_name = app_launch_config[key][
                            "bin_path"] + " " + ' '.join(
                                mdc_base_app_config[app_list][key]
                                ["Arguments"])
                        full_process_names.add(full_process_name.strip())
            except KeyError, e:
                print('KeyError:%s' % e)
                continue
        process_dict = client.parse_processes(full_process_names)
        for process in process_dict:
            if len(set(process_dict[process])) != 1:
                print('Failed process:%s with pid %s' %
                      (process, ' '.join(process_dict[process])))
            else:
                print('Success process:%s with pid %s' %
                      (process, ' '.join(process_dict[process])))
    finally:
        client.close()


if __name__ == '__main__':
    main('10.246.55.69', 'root', 'Huawei12#$')
