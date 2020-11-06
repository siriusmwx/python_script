import os
from shutil import copy
from PIL import Image

username = os.environ['USERNAME']
wall_src_dir="C:\\Users\\"+username+"\\AppData\\Local\\Packages\\\
Microsoft.Windows.ContentDeliveryManager_cw5n1h2txyewy\\LocalState\\Assets"
wall_desktop_dir=os.path.join(os.path.dirname(__file__),"desktop")
if not os.path.exists(wall_desktop_dir):os.mkdir(wall_desktop_dir)
wall_moblie_dir=os.path.join(os.path.dirname(__file__),"mobile")
if not os.path.exists(wall_moblie_dir):os.mkdir(wall_moblie_dir)

def file_in_path(file,file_path):
    if file+".jpg" in os.listdir(file_path):
        return True
    return False

for wallpaper in os.listdir(wall_src_dir):
    wallpaper_file=os.path.join(wall_src_dir,wallpaper)
    try:
        im=Image.open(wallpaper_file)
    except IOError:
        print("This isn't a picture.", wallpaper)
    else:
        if im.size[0]==1920:
            im.close()
            if not file_in_path(wallpaper,wall_desktop_dir):
                copy(wallpaper_file,os.path.join(wall_desktop_dir,wallpaper+".jpg"))
        elif im.size[0]==1080:
            im.close()
            if not file_in_path(wallpaper,wall_moblie_dir):
                copy(wallpaper_file,os.path.join(wall_moblie_dir,wallpaper+".jpg"))
        else:im.close()
