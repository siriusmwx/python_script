#!/usr/bin/python3
import os
import re
import signal
import argparse
from subprocess import Popen, run, PIPE, DEVNULL

basename = os.path.basename(__file__)
# Basic console colors
colors = {
    'W': '\033[0m',  # white (normal)
    'R': '\033[31m',  # red
    'G': '\033[32m',  # green
    'O': '\033[33m',  # orange
    'B': '\033[34m',  # blue
    'P': '\033[35m',  # purple
    'C': '\033[36m',  # cyan
    'GR': '\033[37m',  # gray
    'D': '\033[2m'   # dims current color. {W} resets.
}

# Helper string replacements
replacements = {
    '{+}': '{W}{D}[{W}{G}+{W}{D}]{W}',
    '{!}': '{W}{D}[{W}{R}!{W}{D}]{W}',
    '{?}': '{W}{D}[{W}{C}?{W}{D}]{W}'
}


def color(text):
    ''' Returns colored string '''
    output = text
    for (key, value) in replacements.items():
        output = output.replace(key, value)
    for (key, value) in colors.items():
        output = output.replace('{%s}' % key, value)
    return output


def ConfirmRunningAsRoot():
    if os.getuid() != 0:
        print(
            color("{!} {O}ERROR: {G}" + basename +
                  "{W} must be run as {R}root.{W}"))
        exit(1)


class Disk:

    def __init__(self, disk):
        self.disk = disk[5:]
        self.disk_path = os.path.join('/sys/block', self.disk)
        self.device = disk
        self.get_disk_info()
        self.efi_flag = False
        if os.path.exists('/sys/firmware/efi'):
            self.efi_flag = True
        self.mount_info = {}
        self.get_mount_info()
        if self.mount_info:
            self.umount_all()

    def get_disk_info(self):
        with open(os.path.join(self.disk_path, 'size')) as f:
            self.block = int(f.readline())
        with open(os.path.join(self.disk_path, 'queue', 'logical_block_size')) as f:
            self.logical_block_byte = int(f.readline())
        self.size = '%.2f' % (
            self.block * self.logical_block_byte / 1073741824)

    def get_mount_info(self):
        proc = run(['df'], stdout=PIPE, stderr=DEVNULL,
                   universal_newlines=True)
        mount_infos = proc.stdout.strip().split('\n')
        pattern = re.compile('^(%s\\d+)[ ].*[ ](/\\w*)$' % self.device, re.I)
        for mount_info in mount_infos:
            match = re.search(pattern, mount_info)
            if match:
                self.mount_info[match.group(1)] = match.group(2)

    def umount_all(self):
        mount_list = sorted(self.mount_info.items(),
                            key=lambda x: x[1].count('/'), reverse=True)
        device_list = [x[0] for x in mount_list]
        for device in device_list:
            self.umount_device(device)

    def mount_device(self, device, mount_point):
        if device not in self.mount_info:
            if self.mount(device, mount_point):
                print(color('{+} {G}Success{O} to mount {C}%s{W} to {G}%s{W}.'
                            % (device, mount_point)))
                self.mount_info[device] = mount_point
            else:
                print(color('{!} {R}Fail{O} to mount {C}%s{W} to {G}%s{W}.'
                            % (device, mount_point)))
                exit(1)
        else:
            print(color('{!} {C}%s{O} has mounted on {G}%s{O}!{W}'
                        % (device, self.mount_info[device])))

    def umount_device(self, device):
        if device in self.mount_info:
            if self.umount(device):
                print(color('{+} {G}Success{O} to umount {C}%s{O} from {G}%s{W}.'
                            % (device, self.mount_info[device])))
                del self.mount_info[device]
            else:
                print(color('{!} {R}Fail{O} to umount {C}%s{O} from {G}%s{W}.'
                            % (device, self.mount_info[device])))
                exit(1)
        else:
            print(color('{!} {C}%s{O} does not mounted!{W}' % (device)))

    @staticmethod
    def mount(device, mount_point):
        proc = run(['mount', device, mount_point],
                   stdout=DEVNULL, stderr=DEVNULL)
        if proc.returncode == 0:
            return True
        else:
            return False

    @staticmethod
    def umount(device):
        proc = run(['umount', device], stdout=DEVNULL, stderr=DEVNULL)
        if proc.returncode == 0:
            return True
        else:
            return False

    def _gpt_partion(self):
        print(color(
            "{+} {O}Starting covert {C}%s{O} to {G}GPT{O} Partition,please waiting...{W}" % (self.disk)))
        start_sector = 2048
        efi_part_in_byte = 134217728
        end_sector = (efi_part_in_byte //
                      self.logical_block_byte) - 1 + start_sector
        proc = Popen(['fdisk', self.device], stdin=PIPE,
                     stdout=DEVNULL, stderr=DEVNULL, universal_newlines=True)
        proc.communicate(
            'g\nn\n\n\n%s\nn\n\n\n\nt\n1\n1\nt\n2\n20\nw\n' % (end_sector))
        if proc.returncode == 0:
            print(color(
                "{+} {G}Successed{O} to covert {C}%s{O} to {G}EFI & System{O} partitions.{W}" % (self.disk)))
        else:
            print(color(
                "{!} {R}Failed{O} to covert {C}%s{O} to {G}EFI & System{O} partitions.{W}" % (self.disk)))
            exit(1)
        print(color(
            "{+} {O}Starting format {C}%s{O} to {G}Fat32{O} Partition,waiting...{W}" % (self.disk + '1')))
        self.get_mount_info()
        self.umount_device(self.device + '1')
        proc = Popen(['mkfs.vfat', self.device + '1'],
                     stdin=PIPE, stdout=DEVNULL, stderr=DEVNULL)
        proc.communicate(b'y\n')
        if proc.returncode == 0:
            print(color(
                "{+} {G}Successed{O} to format {C}%s{O} to {G}Fat32{O} filesystem.{W}" % (self.disk + '1')))
        else:
            print(color(
                "{!} {R}Failed{O} to format {C}%s{O} to {G}Fat32{O} filesystem.{W}" % (self.disk + '1')))
            exit(1)
        self.efi_uuid = run(['grub-probe', '--device', self.device + '1', '--target=fs_uuid'],
                            stdout=PIPE, universal_newlines=True).stdout.strip()
        print(color(
            "{+} {O}Starting format {C}%s{O} to {G}Ext4{O} Partition,waiting...{W}" % (self.disk + '2')))
        self.umount_device(self.device + '2')
        proc = Popen(['mkfs.ext4', self.device + '2', '-L', 'SYSTEM'],
                     stdin=PIPE, stdout=DEVNULL, stderr=DEVNULL)
        proc.communicate(b'y\n')
        if proc.returncode == 0:
            print(color(
                "{+} {G}Successed{O} to format {C}%s{O} to {G}Ext4{O} filesystem.{W}" % (self.disk + '2')))
        else:
            print(color(
                "{!} {R}Failed{O} to format {C}%s{O} to {G}Ext4{O} filesystem.{W}" % (self.disk + '2')))
            exit(1)
        self.sys_uuid = run(['grub-probe', '--device', self.device + '2', '--target=fs_uuid'],
                            stdout=PIPE, universal_newlines=True).stdout.strip()

    def _dos_partion(self):
        print(color(
            "{+} {O}Starting covert {C}%s{O} to {G}DOS{O} Partition,please waiting...{W}" % (self.disk)))
        proc = Popen(['fdisk', self.device], stdin=PIPE,
                     stdout=DEVNULL, stderr=DEVNULL, universal_newlines=True)
        proc.communicate('o\nn\np\n\n\n\nt\n83\na\nw\n')
        if proc.returncode == 0:
            print(color(
                "{+} {G}Successed{O} to covert {C}%s{O} to {G}System{O} partition.{W}" % (self.disk)))
        else:
            print(color(
                "{!} {R}Failed{O} to covert {C}%s{O} to {G}System{O} partition.{W}" % (self.disk)))
            exit(1)
        print(color(
            "{+} {O}Starting format {C}%s{O} to {G}Ext4{O} Partition,waiting...{W}" % (self.disk + '1')))
        self.get_mount_info()
        self.umount_device(self.device + '1')
        proc = Popen(['mkfs.ext4', self.device + '1', '-L', 'SYSTEM'],
                     stdin=PIPE, stdout=DEVNULL, stderr=DEVNULL)
        proc.communicate(b'y\n')
        if proc.returncode == 0:
            print(color(
                "{+} {G}Successed{O} to format {C}%s{O} to {G}Ext4{O} filesystem.{W}" % (self.disk + '1')))
        else:
            print(color(
                "{!} {R}Failed{O} to format {C}%s{O} to {G}Ext4{O} filesystem.{W}" % (self.disk + '1')))
            exit(1)
        self.root_uuid = run(['grub-probe', '--device', self.device + '1', '--target=fs_uuid'],
                             stdout=PIPE, universal_newlines=True).stdout.strip()

    def creat_partiton(self):
        if self.efi_flag:
            print(color("{!} {O}Found {G}EFI {O}Environment{W}"))
            self._gpt_partion()
        else:
            print(color("{!} {O}Found {G}DOS {O}Environment{W}"))
            self._dos_partion()


def install_grub(disk, mount_point):
    print(color(
        "\n{+} {O}Starting to install grub to {G}%s{O},please waiting...{W}" % (disk)))
    proc = run(['mount', '--bind', '/dev', '%s/dev' % (mount_point)])
    proc = run(['mount', '--bind', '/proc', '%s/proc' % (mount_point)])
    proc = run(['mount', '--bind', '/sys', '%s/sys' % (mount_point)])
    proc = Popen(['chroot', mount_point], stdin=PIPE, universal_newlines=True)
    proc.communicate("grub-install %s\nupdate-grub\n" % (disk))
    if proc.returncode == 0:
        print(color(
            "{+} {G}Successed{O} to install grub to {G}%s.{W}" % (disk)))
    else:
        print(color(
            "{+} {R}Failed{O} to install grub to {G}%s.{W}" % (disk)))


def system_recovery(disk, backup, mount_point='/mnt'):
    if not os.path.exists(mount_point):
        os.makedirs(mount_point)
    device = Disk(disk)
    device.creat_partiton()
    if device.efi_flag:
        device.mount_device(disk + '2', mount_point)
    else:
        device.mount_device(disk + '1', mount_point)
    proc = Popen(['tar', '-xvpzf', backup, '-C', mount_point],
                 stdout=PIPE, stderr=PIPE, universal_newlines=True)
    print(color("{+} {O}Starting extract {C}%s{O} to {G}%s{O},Waiting or {R}Ctrl+C{O} Interrupt{W}"
                % (backup, mount_point)))
    try:
        while proc.poll() == None:
            stdout = proc.stdout.readline().rstrip()
            if stdout:
                if len(stdout) > 50:
                    stdout = stdout[0:47] + '...'
                print(color(
                    "\r{+} {O}Extracting: {C}%-50s{W}" % (stdout)), end='')
    except KeyboardInterrupt:
        proc.send_signal(signal.SIGINT)
        print(color("\n{!} {R}(^C) {O}Control-C Interrupt{W}"))
        device.umount_all()
        exit(1)
    print(
        color("\n{+} {O}Starting rewrite {G}%s/etc/fstab{O} file.{W}" % (mount_point)))
    with open('%s/etc/fstab' % (mount_point), 'w') as f:
        f.write(
            "# <file system> <mount point>   <type>  <options>       <dump>  <pass>\n")
        if device.efi_flag:
            if not os.path.exists('%s/boot/efi' % (mount_point)):
                os.makedirs('%s/boot/efi' % (mount_point))
            device.mount_device(disk + '1', '%s/boot/efi' % (mount_point))
            f.write("# / was on /dev/sda2 during installation\n")
            f.write(
                "UUID=%s /               ext4    errors=remount-ro 0       1\n" % (device.sys_uuid))
            f.write("# /boot/efi was on /dev/sda1 during installation\n")
            f.write(
                "UUID=%s  /boot/efi       vfat    umask=0077      0       1\n" % (device.efi_uuid))
        else:
            f.write("# / was on /dev/sda1 during installation\n")
            f.write(
                "UUID=%s /               ext4    errors=remount-ro 0       1\n" % (device.root_uuid))
        f.write("/swapfile   none            swap    sw              0       0\n")
    install_grub(disk, mount_point)
    device.umount_all()


def main():
    parser = argparse.ArgumentParser(
        description='Python3 script to recovery system to a disk with tar.gz archive backup')
    parser.add_argument('disk', metavar='DISK',
                        help='a disk prepare to partion and recovery system,e.g /dev/sdb')
    parser.add_argument('file', metavar='BACKUP',
                        help='a backup file compressed with tar.gz')
    options = parser.parse_args()
    ConfirmRunningAsRoot()
    if os.path.exists(options.disk) and os.path.exists(options.file) and \
            options.disk.startswith('/dev/') and options.file.endswith('.tgz'):
        disk, backup = options.disk, options.file
    else:
        parser.print_help()
        print('\nexample: ' + basename + ' /dev/sdc backup.tgz')
        exit(1)
    system_recovery(disk, backup)

if __name__ == '__main__':
    main()
