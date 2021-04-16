# -*- coding:utf-8 -*-
import os
import re
import sys
import fnmatch

os.system('')
# Basic console colors
W = '\033[0m'  # white (normal)
R = '\033[31m'  # red
G = '\033[32m'  # green
O = '\033[33m'  # orange
B = '\033[34m'  # blue
P = '\033[35m'  # purple
C = '\033[36m'  # cyan
GR = '\033[37m'  # gray
D = '\033[2m'  # dims current color. {W} resets.


def content_search(file, pattern):
    i = 0
    try:
        with open(file) as f:
            for line in f:
                i += 1
                result = pattern.search(line)
                if result:
                    return ('%s%s%s' % (O, i, W) + '::' +
                            line.replace(result.group(), '%s%s%s' %
                                         (C, result.group(), W)))
    except:
        pass
    return ''


def file_search(dir_path, fn_pattern, pattern):
    try:
        for root, dirs, files in os.walk(dir_path):
            for file in files:
                if fnmatch.fnmatch(file, fn_pattern):
                    file_path = os.path.join(root, file)
                    if pattern:
                        result = content_search(file_path, pattern).rstrip()
                        if result:
                            print('%s%s%s::%s' % (G, file_path, W, result))
                    else:
                        print('%s%s%s' % (G, file_path, W))
    except KeyboardInterrupt:
        print("")
        print('%sDetect KeyboardInterrupt!%s' % (R, W))


if __name__ == '__main__':
    # print(sys.argv)
    try:
        dir_path = os.path.realpath(sys.argv[1])
        fn_pattern = sys.argv[2]
    except IndexError:
        print('args must be 2 or 3')
        sys.exit(-1)
    if not os.path.isdir(dir_path):
        print('the dir %s%s%s not exist!' % (O, dir_path, W))
        sys.exit(-1)
    try:
        pattern = re.compile(sys.argv[3], re.I)
    except:
        pattern = None
    file_search(dir_path, fn_pattern, pattern)
