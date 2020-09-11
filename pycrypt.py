#!/usr/bin/python3
from Crypto import Random
from Crypto.Cipher import AES


class Encryptor:

    key = Random.new().read(32)  # 16,24 or 32
    bs = AES.block_size

    def _pad(self, s):
        if chr(s[-1]) != '#':
            bt = '#'.encode()
        else:
            bt = '$'.encode()
        if len(s) < self.bs:
            s += (self.bs - len(s)) * bt
        elif len(s) % self.bs == 0:
            s += 16 * bt
        else:
            s += (self.bs - len(s) % self.bs) * bt
        return s

    @classmethod
    def encrypt(cls, message):
        iv = Random.new().read(cls.bs)
        cipher = AES.new(cls.key, AES.MODE_CBC, iv)
        ciphertext = iv + cipher.encrypt(cls._pad(cls, message))
        return ciphertext

    @classmethod
    def encrypt_file(cls, file_name):
        with open(file_name, 'rb') as fo:
            plaintext = fo.read()
        enc = cls.encrypt(plaintext)
        with open(file_name + ".enc", 'wb') as fo:
            fo.write(enc)

    @classmethod
    def decrypt(cls, ciphertext):
        unpad = lambda s: s.rstrip(chr(s[-1]).encode())
        iv = ciphertext[:cls.bs]
        cipher = AES.new(cls.key, AES.MODE_CBC, iv)
        plaintext = unpad(cipher.decrypt(ciphertext[cls.bs:]))
        return plaintext

    @classmethod
    def decrypt_file(cls, file_name):
        with open(file_name, 'rb') as fo:
            ciphertext = fo.read()
        dec = cls.decrypt(ciphertext)
        with open(file_name[:-4], 'wb') as fo:
            fo.write(dec)


if __name__ == '__main__':
    try:
        import sys
        if sys.argv[1] == '-e':
            Encryptor.encrypt_file(sys.argv[2])
        elif sys.argv[1] == '-d':
            Encryptor.decrypt_file(sys.argv[2])
    except:
        pass
