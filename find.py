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

# print(sys.argv)
try:
    path = sys.argv[1]
    name = sys.argv[2]
except:
    print('args must be 2 or 3')
    sys.exit(-1)
try:
    math = re.compile(sys.argv[3], re.I)
except:
    math = None


def search(file, math):
    i = 0
    with open(file) as f:
        for line in f:
            i += 1
            result = math.search(line)
            if result:
                return ('%s%s%s' % (O, i, W) + '::' +
                        line.replace(result.group(), '%s%s%s' %
                                     (C, result.group(), W)))
    return ''


if __name__ == '__main__':
    for root, dirs, files in os.walk(path):
        for file in files:
            if fnmatch.fnmatch(file, name):
                filepath = os.path.join(root, file)
                if math:
                    result = search(filepath, math).rstrip()
                    if result:
                        print('%s%s%s::%s' % (G, filepath, W, result))
                else:
                    print('%s%s%s' % (G, filepath, W))
