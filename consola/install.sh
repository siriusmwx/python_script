#!/bin/bash
# wget https://down.gloriousdays.pw/Fonts/Consolas.zip
# unzip Consolas.zip
mkdir -p /usr/share/fonts/consolas
cp consola*.ttf /usr/share/fonts/consolas/
chmod 644 /usr/share/fonts/consolas/consola*.ttf
cd /usr/share/fonts/consolas
mkfontscale && mkfontdir && fc-cache -fv
