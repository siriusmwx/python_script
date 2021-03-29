import os
import zipfile
import tarfile


def compress_to_zip(file):
    file = os.path.abspath(file)
    if os.path.isfile(file):
        with zipfile.ZipFile(os.path.splitext(file)[0]+'.zip', mode="w",
                             compression=zipfile.ZIP_DEFLATED, compresslevel=6) as zf:
            zf.write(file, arcname=os.path.basename(file))
    elif os.path.isdir(file):
        with zipfile.ZipFile(file+'.zip', mode="w",
                             compression=zipfile.ZIP_DEFLATED, compresslevel=6) as zf:
            for dirpath, dirnames, filenames in os.walk(file):
                for filename in filenames:
                    file_path = os.path.join(dirpath, filename)
                    zf.write(file_path,
                             arcname=os.path.relpath(file_path, start=os.path.dirname(file)))


def compress_to_tar(file):
    file = os.path.abspath(file)
    if os.path.isfile(file):
        with tarfile.open(os.path.splitext(
                file)[0]+'.tgz', mode="w:gz", compresslevel=6) as tf:
            tf.add(file, arcname=os.path.basename(file))
    elif os.path.isdir(file):
        with tarfile.open(file+'.tgz', mode="w:gz", compresslevel=6) as tf:
            for dirpath, dirnames, filenames in os.walk(file):
                subdir = os.path.join(os.path.basename(
                    file), dirpath.split(file)[-1].lstrip('\\'))
                for filename in filenames:
                    file_path = os.path.join(dirpath, filename)
                    tf.add(file_path,
                           arcname=os.path.relpath(file_path, start=os.path.dirname(file)))


if __name__ == '__main__':
    compress_to_zip(r'D:\Programs\extensions')
    compress_to_tar(r'D:\Programs\extensions')
