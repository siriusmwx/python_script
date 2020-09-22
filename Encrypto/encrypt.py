#!/usr/bin/python3
import argparse
from pathlib import Path
from pycrypto import AES_Cryptor, RSA_Cryptor


def dump_keys(path='keys'):
    path_dir = Path(path)
    path_dir.mkdir(parents=True, exist_ok=True)
    RSA_Cryptor.gen_key()
    with open(Path(path_dir, 'public.pem'), 'wb') as f:
        f.write(RSA_Cryptor.public_key)
    with open(Path(path_dir, 'private.key'), 'wb') as f:
        f.write(RSA_Cryptor.private_key)


def load_keys(path='keys'):
    public_path = Path(path, 'public.pem')
    private_path = Path(path, 'private.key')
    if public_path.is_file():
        with open(public_path, 'rb') as f:
            RSA_Cryptor.public_key = f.read()
    if private_path.is_file():
        with open(private_path, 'rb') as f:
            RSA_Cryptor.private_key = f.read()


def arg_parser():
    parser = argparse.ArgumentParser(
        description='一个简单的用于AES、RSA加密解密的命令行脚本')
    aes = parser.add_argument_group('AES Crypto')
    aes.add_argument('-k', '--key', metavar='password',
                     help="用于AES加密解密所需的密钥")
    aes.add_argument('-e', metavar='message', dest='enc',
                     help="指定需要使用AES加密的信息")
    aes.add_argument('-d', metavar='message', dest='dec',
                     help="指定需要使用AES解密的信息")
    aes.add_argument('-E', nargs='+', metavar='file', dest='ENC',
                     help="指定需要AES加密的文件，可为多个文件")
    aes.add_argument('-D', nargs='+', metavar='file', dest='DEC',
                     help="指定需要AES解密的文件，可为多个文件")
    rsa = parser.add_argument_group('RSA Crypto')
    rsa.add_argument('--dump', metavar='key_dir',
                     help='生成RSA公私钥对，并保存至指定文件夹')
    rsa.add_argument('--load', metavar='key_dir', default='keys',
                     help='从指定的文件夹加载公钥与私钥，默认为keys文件夹')
    rsa.add_argument('--enc', metavar='message', dest='Enc',
                     help="指定需要使用RSA加密的信息")
    rsa.add_argument('--dec', metavar='message', dest='Dec',
                     help="指定需要使用RSA解密的信息")
    return parser


def print_help(basename):
    print('\nexample: ' + basename + ' -k password -e message \tAES')
    print('         ' + basename + ' -k password -d message \tAES')
    print('         ' + basename + ' -k password -E file1 file2')
    print('         ' + basename + ' -k password -D file1 file2')
    print('         ' + basename + ' --dump key_dir')
    print('         ' + basename + ' --enc message \tRSA')
    print('         ' + basename + ' --dec message \tRSA')
    exit(1)


def main():
    parser = arg_parser()
    args = parser.parse_args()
    basename = Path(__file__).name
    if args.key:
        AES_Cryptor.gen_key(args.key)
        if args.enc:
            cipherdata = AES_Cryptor.encrypt(args.enc.encode()).decode()
            print(cipherdata)
        elif args.dec:
            plaindata = AES_Cryptor.decrypt(args.dec.encode()).decode()
            print(plaindata)
        elif args.ENC:
            for file in args.ENC:
                AES_Cryptor.encrypt_file(file)
        elif args.DEC:
            for file in args.DEC:
                AES_Cryptor.decrypt_file(file)
        else:
            parser.print_usage()
            print_help(basename)
    elif args.Enc:
        load_keys(args.load)
        if not RSA_Cryptor.public_key:
            print('Please make sure the public.pem file was in the keys dir')
            print('Or use --load option to specify a dir contains public_key file')
            exit(1)
        cipherdata = RSA_Cryptor.encrypt(args.Enc.encode()).decode()
        print(cipherdata)
    elif args.Dec:
        load_keys(args.load)
        if not RSA_Cryptor.private_key:
            print('Please make sure the private.key file was in the keys dir')
            print('Or use --load option to specify a dir contains private_key file')
            exit(1)
        plaindata = RSA_Cryptor.decrypt(args.Dec.encode()).decode()
        print(plaindata)
    elif args.dump:
        dump_keys(args.dump)
    else:
        parser.print_usage()
        print_help(basename)

if __name__ == '__main__':
    main()
