#!/usr/bin/python3
from tkinter import *
from pycrypto import AES_Cryptor


def set_key():
    password = key.get()
    AES_Cryptor.gen_key(password)
    print('KEY:', AES_Cryptor.key)


def enc_msg():
    message = enc_txt.get('0.0', 'end').rstrip()
    if not (message and AES_Cryptor.key):
        return
    enc_txt.delete('0.0', 'end')
    ciphertext = AES_Cryptor.encrypt(message.encode())
    print('ENC_MSG:', ciphertext)
    dec_txt.delete('0.0', 'end')
    dec_txt.insert('0.0', ciphertext.decode())


def dec_msg():
    message = dec_txt.get('0.0', 'end').rstrip()
    if not (message and AES_Cryptor.key):
        return
    dec_txt.delete('0.0', 'end')
    plaintext = AES_Cryptor.decrypt(message.encode())
    print('DEC_MSG:', plaintext)
    enc_txt.delete('0.0', 'end')
    enc_txt.insert('0.0', plaintext.decode())

window = Tk()
window.title('加密解密小工具')
frame = Frame(window)
frame.pack()
Label(frame, text='先输入密钥，再点击<设置密钥>按钮', bg='gray',
      font=('Arial', 14)).grid(columnspan=50, ipady=3, pady=2, sticky='news')
Label(frame, text='PassWord', bg='green',
      font=('Arial', 14)).grid(columnspan=12, sticky='news')
key = Entry(frame, show='*', font=('Arial', 14))
key.grid(row=1, column=12, columnspan=30, sticky='news')
Button(frame, text='设置密钥', font=('Arial', 12), bg='gray', fg='blue',
       command=set_key).grid(row=1, column=42, columnspan=8, sticky='news')
enc_txt = Text(frame, show=None, font=('Arial', 14), width=20, height=10)
enc_txt.grid(row=2, rowspan=2, columnspan=22,
             padx=2, pady=2, sticky='news')
Button(frame, text='加密==>', font=('Arial', 10), bg='orange', height=2,
       command=enc_msg).grid(row=2, column=22, columnspan=6, sticky='ew')
Button(frame, text='<==解密', font=('Arial', 10), bg='orange', height=2,
       command=dec_msg).grid(row=3, column=22, columnspan=6, sticky='ew')
dec_txt = Text(frame, show=None, font=('Arial', 14), width=20, height=10)
dec_txt.grid(row=2, column=28, rowspan=2,
             columnspan=22, padx=2, pady=2, sticky='news')


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(
        description='一个简单的脚本用于加密解密文件')
    parser.add_argument('-k', '--key', metavar='password',
                        help="用于加密解密文件所需的密钥")
    parser.add_argument('-e', '--enc', nargs='+', metavar='file',
                        help="指定需要加密的文件名路径，可以为多个文件")
    parser.add_argument('-d', '--dec', nargs='+', metavar='file',
                        help="指定需要解密的文件名路径，可以为多个文件")
    args = parser.parse_args()
    if args.key:
        AES_Cryptor.gen_key(args.key)
        if args.enc:
            for file in args.enc:
                AES_Cryptor.encrypt_file(file)
        elif args.dec:
            for file in args.dec:
                AES_Cryptor.decrypt_file(file)
        else:
            import os
            basename = os.path.basename(__file__)
            parser.print_help()
            print('\nexample: ' + basename + ' -k password -e file1 file2')
            print('         ' + basename + ' -k password -d file1 file2')
    else:
        window.mainloop()
