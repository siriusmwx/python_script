# -*- coding:utf-8 -*-
from __future__ import print_function
import os
import sys
import paramiko


def bytes_to_str(bytes_or_str):
    if isinstance(bytes_or_str, bytes):
        value = bytes_or_str.decode('utf-8')
    else:
        value = bytes_or_str
    return value


class SSHConnection:
    def __init__(self, hostname, username, password, port=22):
        self.host = hostname
        self.port = port
        self.username = username
        self.pwd = password
        self.__k = None

    def connect(self):
        transport = paramiko.Transport((self.host, self.port))
        transport.connect(username=self.username, password=self.pwd)
        self.__transport = transport

    def close(self):
        self.__transport.close()

    def run_cmd(self, command, timeout=0.5, environment=None):
        ssh = paramiko.SSHClient()
        ssh._transport = self.__transport
        stdin, stdout, stderr = ssh.exec_command(command,
                                                 timeout=timeout,
                                                 environment=environment)
        return bytes_to_str(stdout.read()), bytes_to_str(stderr.read())

    def upload(self, local_path, target_path):
        sftp = paramiko.SFTPClient.from_transport(self.__transport)
        sftp.put(local_path, target_path, confirm=True)
        sftp.chmod(target_path, 0o755)

    def download(self, target_path, local_path):
        sftp = paramiko.SFTPClient.from_transport(self.__transport)
        sftp.get(target_path, local_path)


if __name__ == '__main__':
    client.connect()
    stdout, stderr = client.run_cmd(r'df -h')
    print(stdout)
    print(stderr)
    
