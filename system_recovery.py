#!/usr/bin/python3
import os
import sys
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
        self.dev_path = disk
        self.get_disk_info()
        self.efi_flag = False
        if os.path.exists('/sys/firmware/efi'):
            self.efi_flag = True

    def get_disk_info(self):
        with open(os.path.join(self.disk_path, 'size')) as f:
            self.block = int(f.readline())
        with open(os.path.join(self.disk_path, 'queue', 'logical_block_size')) as f:
            self.logical_block_byte = int(f.readline())
        self.size = '%.2f' % (
            self.block * self.logical_block_byte / 1073741824)

    def _gpt_partion(self):
        print(color(
            "{+} {O}Starting covert {C}%s{O} to {G}GPT{O} Partition,please waiting...{W}" % (self.disk)))
        start_sector = 2048
        efi_part_in_byte = 134217728
        end_sector = (efi_part_in_byte //
                      self.logical_block_byte) - 1 + start_sector
        proc = run(['umount', self.dev_path + '*'])
        proc = Popen(['fdisk', self.dev_path], stdin=PIPE,
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
        proc = run(['umount', self.dev_path + '1'])
        proc = Popen(['mkfs.vfat', self.dev_path + '1'],
                     stdin=PIPE, stdout=DEVNULL, stderr=DEVNULL)
        proc.communicate(b'y\n')
        if proc.returncode == 0:
            print(color(
                "{+} {G}Successed{O} to format {C}%s{O} to {G}Fat32{O} filesystem.{W}" % (self.disk + '1')))
        else:
            print(color(
                "{!} {R}Failed{O} to format {C}%s{O} to {G}Fat32{O} filesystem.{W}" % (self.disk + '1')))
            exit(1)
        self.efi_uuid = run(['grub-probe', '--device', self.dev_path + '1', '--target=fs_uuid'],
                            stdout=PIPE, universal_newlines=True).stdout.strip()
        print(color(
            "{+} {O}Starting format {C}%s{O} to {G}Ext4{O} Partition,waiting...{W}" % (self.disk + '2')))
        proc = run(['umount', self.dev_path + '2'])
        proc = Popen(['mkfs.ext4', self.dev_path + '2', '-L', 'SYSTEM'],
                     stdin=PIPE, stdout=DEVNULL, stderr=DEVNULL)
        proc.communicate(b'y\n')
        if proc.returncode == 0:
            print(color(
                "{+} {G}Successed{O} to format {C}%s{O} to {G}Ext4{O} filesystem.{W}" % (self.disk + '2')))
        else:
            print(color(
                "{!} {R}Failed{O} to format {C}%s{O} to {G}Ext4{O} filesystem.{W}" % (self.disk + '2')))
            exit(1)
        self.sys_uuid = run(['grub-probe', '--device', self.dev_path + '2', '--target=fs_uuid'],
                            stdout=PIPE, universal_newlines=True).stdout.strip()

    def _dos_partion(self):
        print(color(
            "{+} {O}Starting covert {C}%s{O} to {G}DOS{O} Partition,please waiting...{W}" % (self.disk)))
        proc = run(['umount', self.dev_path + '*'])
        proc = Popen(['fdisk', self.dev_path], stdin=PIPE,
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
        proc = run(['umount', self.dev_path + '1'])
        proc = Popen(['mkfs.ext4', self.dev_path + '1', '-L', 'SYSTEM'],
                     stdin=PIPE, stdout=DEVNULL, stderr=DEVNULL)
        proc.communicate(b'y\n')
        if proc.returncode == 0:
            print(color(
                "{+} {G}Successed{O} to format {C}%s{O} to {G}Ext4{O} filesystem.{W}" % (self.disk + '1')))
        else:
            print(color(
                "{!} {R}Failed{O} to format {C}%s{O} to {G}Ext4{O} filesystem.{W}" % (self.disk + '1')))
            exit(1)
        self.root_uuid = run(['grub-probe', '--device', self.dev_path + '1', '--target=fs_uuid'],
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
        "{+} {O}Starting to install grub to {G}%s{O},please waiting...{W}" % (disk)))
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
        exit(1)


def system_recovery(disk, backup, mount_point='/mnt'):
    if not os.path.exists(mount_point):
        os.makedirs(mount_point)
    dev = Disk(disk)
    dev.creat_partiton()
    proc = run(['umount', disk + '*'])
    if dev.efi_flag:
        proc = run(['mount', disk + '2', mount_point])
    else:
        proc = run(['mount', disk + '1', mount_point])
    proc = Popen(['tar', '-xvpzf', backup, '-C', mount_point],
                 stdout=PIPE, stderr=DEVNULL, universal_newlines=True)
    print(color("{+} {O}Start to extract {C}%s{O} to {G}%s{O},Waiting or {R}Ctrl+C{O} Interrupt{W}"
                % (backup, mount_point)))
    try:
        while proc.poll() == None:
            stdout = proc.stdout.readline().strip()
            if stdout:
                if len(stdout) > 50:
                    stdout = stdout[0:48] + '...'
                sys.stdout.write(
                    color("\r{+} {O}Extracting: {C}%-50s{W}" % (stdout)))
                sys.stdout.flush()
    except KeyboardInterrupt:
        proc.send_signal(signal.SIGINT)
        print(color("\n{!} {R}(^C) {O}Control-C Interrupt{W}"))
        exit(1)
    with open('%s/etc/fstab' % (mount_point), 'w') as f:
        f.write(
            "# <file system> <mount point>   <type>  <options>       <dump>  <pass>\n")
        if dev.efi_flag:
            proc = run(['mount', disk + '1', '%s/boot/efi' % (mount_point)])
            f.write("# / was on /dev/sda2 during installation\n")
            f.write(
                "UUID=%s /               ext4    errors=remount-ro 0       1\n" % (dev.sys_uuid))
            f.write("# /boot/efi was on /dev/sda1 during installation\n")
            f.write(
                "UUID=%s  /boot/efi       vfat    umask=0077      0       1\n" % (dev.efi_uuid))
        else:
            f.write("# / was on /dev/sda1 during installation\n")
            f.write(
                "UUID=%s /               ext4    errors=remount-ro 0       1\n" % (dev.root_uuid))
        f.write("/swapfile   none            swap    sw              0       0\n")
    install_grub(disk, mount_point)


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
