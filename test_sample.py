# -*- coding:utf-8 -*-
from __future__ import print_function
import pytest


class TestClass:
    @pytest.fixture(scope="function")
    def setup(self, request):
        def teardown():
            print("teardown is called \n")

        request.addfinalizer(teardown)
        print("setup is called\n")

    def test_case001(self, setup):
        print('start testing')
        print(AsciiStr2CharStr('12345678'))


def AsciiStr2CharStr(asciiStr):
    charStr = ''
    if len(asciiStr) % 2 != 0:
        return charStr
    for i in range(0, len(asciiStr) / 2):
        charStr += chr(int(asciiStr[2 * i:2 * i + 2], 16))
    return charStr


if __name__ == '__main__':
    abc = list(chr(x) for x in xrange(100))
    # x = 'NO'
    print(str(7879) + '==>' + AsciiStr2CharStr(str(7879)))
    print(int('78', 16))
    print(chr(int('78', 16)))
    
