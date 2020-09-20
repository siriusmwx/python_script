#!/usr/bin/python3
import os
from Crypto import Random
from Crypto.Hash import SHA256
from Crypto.PublicKey import RSA
from Crypto.Cipher import AES, PKCS1_OAEP
from Crypto.Signature import PKCS1_PSS
from base64 import b64encode, b64decode


class AES_Cryptor:

    key = b''
    bs = AES.block_size

    def _pad(self, s):
        if chr(s[-1]) != '+':
            bt = '+'.encode()
        else:
            bt = '-'.encode()
        if len(s) < self.bs:
            s += (self.bs - len(s)) * bt
        else:
            s += (self.bs - len(s) % self.bs) * bt
        return s

    @classmethod
    def gen_key(cls, password):
        if len(password) <= 16:
            cls.key = ('%-16s' % password).encode()
        elif len(password) <= 24:
            cls.key = ('%-24s' % password).encode()
        elif len(password) <= 32:
            cls.key = ('%-32s' % password).encode()
        else:
            cls.key = password[0:32].encode()

    @classmethod
    def encrypt(cls, data):
        if not cls.key:
            return
        iv = Random.new().read(cls.bs)
        cipher = AES.new(cls.key, AES.MODE_CBC, iv)
        cipherdata = iv + cipher.encrypt(cls._pad(cls, data))
        return b64encode(cipherdata)

    @classmethod
    def decrypt(cls, cipherdata):
        if not cls.key:
            return
        cipherdata = b64decode(cipherdata)
        unpad = lambda s: s.rstrip(chr(s[-1]).encode())
        iv = cipherdata[:cls.bs]
        cipher = AES.new(cls.key, AES.MODE_CBC, iv)
        plaindata = unpad(cipher.decrypt(cipherdata[cls.bs:]))
        return plaindata

    @classmethod
    def encrypt_file(cls, file_name):
        with open(file_name, 'rb') as fo:
            plaindata = fo.read()
        enc = cls.encrypt(plaindata)
        with open(file_name + ".enc", 'wb') as fo:
            fo.write(enc)

    @classmethod
    def decrypt_file(cls, file_name):
        with open(file_name, 'rb') as fo:
            cipherdata = fo.read()
        dec = cls.decrypt(cipherdata)
        with open(file_name[:-4], 'wb') as fo:
            fo.write(dec)


class RSA_Cryptor:

    public_key = b''
    private_key = b''
    try:
        Import_Key = RSA.import_key
    except AttributeError:
        Import_Key = RSA.importKey

    @classmethod
    def gen_key(cls):
        key = RSA.generate(2048)
        try:
            cls.private_key = key.export_key()
            cls.public_key = key.publickey().export_key()
        except AttributeError:
            cls.private_key = key.exportKey()
            cls.public_key = key.publickey().exportKey()

    @classmethod
    def encrypt(cls, data):
        if not cls.public_key:
            return
        recipient_key = cls.Import_Key(cls.public_key)
        cipher_rsa = PKCS1_OAEP.new(recipient_key)
        return b64encode(cipher_rsa.encrypt(data))

    @classmethod
    def decrypt(cls, cipherdata):
        if not cls.private_key:
            return
        key = cls.Import_Key(cls.private_key)
        cipher_rsa = PKCS1_OAEP.new(key)
        return cipher_rsa.decrypt(b64decode(cipherdata))

    @classmethod
    def sign(cls, data):
        if not cls.private_key:
            return
        key = cls.Import_Key(cls.private_key)
        _hash = SHA256.new(data)
        signature = PKCS1_PSS.new(key).sign(_hash)
        return b64encode(signature)

    @classmethod
    def verify(cls, data, signature):
        if not cls.public_key:
            return
        key = cls.Import_Key(cls.public_key)
        _hash = SHA256.new(data)
        signature = b64decode(signature)
        return PKCS1_PSS.new(key).verify(_hash, signature)

    @classmethod
    def save_keys(cls, path='keys'):
        if not os.path.exists(path):
            os.mkdir(path)
        if cls.public_key:
            with open(os.path.join(path, 'public.pem'), 'wb') as f:
                f.write(cls.public_key)
        if cls.private_key:
            with open(os.path.join(path, 'private.key'), 'wb') as f:
                f.write(cls.private_key)

    @classmethod
    def load_keys(cls, path='keys'):
        public_path = os.path.join(path, 'public.pem')
        private_path = os.path.join(path, 'private.key')
        if os.path.exists(public_path):
            with open(os.path.join(path, 'public.pem'), 'rb') as f:
                cls.public_key = f.read()
        if os.path.exists(private_path):
            with open(os.path.join(path, 'private.key'), 'rb') as f:
                cls.private_key = f.read()

    # import argparse
    # parser = argparse.ArgumentParser(
    #     description='一个简单的脚本用于加密解密文件')
    # parser.add_argument('-k', '--key', metavar='password',
    #                     help="用于加密解密文件所需的密钥")
    # parser.add_argument('-e', '--enc', nargs='+', metavar='file',
    #                     help="指定需要加密的文件名路径，可以为多个文件")
    # parser.add_argument('-d', '--dec', nargs='+', metavar='file',
    #                     help="指定需要解密的文件名路径，可以为多个文件")
    # args = parser.parse_args()
    # if args.key:
    #     Encryptor.gen_key(args.key)
    #     if args.enc:
    #         for file in args.enc:
    #             Encryptor.encrypt_file(file)
    #     elif args.dec:
    #         for file in args.dec:
    #             Encryptor.decrypt_file(file)
    #     else:
    #         import os
    #         basename = os.path.basename(__file__)
    #         parser.print_help()
    #         print('\nexample: ' + basename + ' -k password -e file1 file2')
    #         print('         ' + basename + ' -k password -d file1 file2')

if __name__ == '__main__':
