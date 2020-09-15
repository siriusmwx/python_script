#!/usr/bin/python3
import base64
from tkinter import *
from Crypto import Random
from Crypto.Cipher import AES


class Encryptor:

    key = None
    bs = AES.block_size

    def _pad(self, s):
        if chr(s[-1]) != '=':
            bt = '='.encode()
        else:
            bt = '_'.encode()
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
    def encrypt(cls, message):
        iv = Random.new().read(cls.bs)
        cipher = AES.new(cls.key, AES.MODE_CBC, iv)
        ciphertext = iv + cipher.encrypt(cls._pad(cls, message))
        return base64.b64encode(ciphertext)

    @classmethod
    def decrypt(cls, ciphertext):
        ciphertext = base64.b64decode(ciphertext)
        unpad = lambda s: s.rstrip(chr(s[-1]).encode())
        iv = ciphertext[:cls.bs]
        cipher = AES.new(cls.key, AES.MODE_CBC, iv)
        plaintext = unpad(cipher.decrypt(ciphertext[cls.bs:]))
        return plaintext

    @classmethod
    def encrypt_file(cls, file_name):
        with open(file_name, 'rb') as fo:
            plaintext = fo.read()
        enc = cls.encrypt(plaintext)
        with open(file_name + ".enc", 'wb') as fo:
            fo.write(enc)

    @classmethod
    def decrypt_file(cls, file_name):
        with open(file_name, 'rb') as fo:
            ciphertext = fo.read()
        dec = cls.decrypt(ciphertext)
        with open(file_name[:-4], 'wb') as fo:
            fo.write(dec)


def set_key():
    password = key.get()
    Encryptor.gen_key(password)
    print(Encryptor.key)


def enc_msg():
    message = enc_txt.get('0.0', 'end').rstrip()
    enc_txt.delete('0.0', 'end')
    ciphertext = Encryptor.encrypt(message.encode())
    print(ciphertext)
    dec_txt.delete('0.0', 'end')
    dec_txt.insert('0.0', ciphertext.decode())


def dec_msg():
    message = dec_txt.get('0.0', 'end').rstrip()
    dec_txt.delete('0.0', 'end')
    plaintext = Encryptor.decrypt(message.encode())
    print(plaintext)
    enc_txt.delete('0.0', 'end')
    enc_txt.insert('0.0', plaintext.decode())

if __name__ == '__main__':
    window = Tk()
    window.title('加密解密小工具')
    frame = Frame(window)
    frame.pack()
    Label(frame, text='说明：先输入密钥，再点击<设置密钥>设置密钥',
          font=('Arial', 14)).grid(columnspan=50, ipady=3, sticky='news')
    Label(frame, text='PassWord', bg='green',
          font=('Arial', 14)).grid(columnspan=12, sticky='news')
    key = Entry(frame, show='*', font=('Arial', 14))
    key.grid(row=1, column=12, columnspan=30, sticky='news')
    Button(frame, text='设置密钥', font=('Arial', 12), bg='gray', fg='blue',
           command=set_key).grid(row=1, column=42, columnspan=8, sticky='news')
    enc_txt = Text(frame, show=None, font=('Arial', 14), width=20, height=10)
    enc_txt.grid(row=2, rowspan=2, columnspan=22,
                 padx=2, pady=2, sticky='news')
    Button(frame, text='加密==>', font=('Arial', 10), bg='orange',
           command=enc_msg).grid(row=2, column=22, columnspan=6, sticky='ew')
    Button(frame, text='<==解密', font=('Arial', 10), bg='orange',
           command=dec_msg).grid(row=3, column=22, columnspan=6, sticky='ew')
    dec_txt = Text(frame, show=None, font=('Arial', 14), width=20, height=10)
    dec_txt.grid(row=2, column=28, rowspan=2,
                 columnspan=22, padx=2, pady=2, sticky='news')
    window.mainloop()
