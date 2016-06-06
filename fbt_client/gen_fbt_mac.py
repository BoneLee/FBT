# coding: utf-8
"""
要成功生成mac下的FBT客户端，需保证有一个和FBT文件夹同级的 node-webkit-version-osx-x64 文件夹
parentdir
|
+--FBT/
+--node-webkit-v0.10.5-osx-x64/  (目前使用)
+--node-webkit-v0.8.6-osx-x64/

How to package and distribute your apps?
Quote from https://github.com/rogerwang/node-webkit/wiki/How-to-package-and-distribute-your-apps

On OS X, the  node-webkit.app is a directory that can be easily changed.
To make node-webkit automatically open your app, you need to put your app
file under  Contents/Resources  and name it app.nw .

The bonus over other platforms is, the  app.nw  needs not to be a zip file,
if you want to speed up startup, you can make  app.nw  your app's directory.
And you need to modify following files to make a real distribution of yours:

   *  Contents/Resources/nw.icns : icon of your app.
   *  Contents/Inffo.plist : the apple package description file.

"""

import shutil
import os
import plistlib
import sys
from os.path import join
from subprocess import Popen
from subprocess import PIPE

if sys.version_info > (3, 4):
    plistload = plistlib.load
    plistdump = plistlib.dump
else:
    plistload = plistlib.readPlist
    plistdump = plistlib.writePlist

gen_fbtmac_script_abspath = os.path.abspath(__file__)
os.chdir(os.path.dirname(gen_fbtmac_script_abspath))

fbtmac_path = '../fbtmac.app'

# clear old stuff
if os.path.exists(fbtmac_path):
    shutil.rmtree(fbtmac_path)

# choose nw version
nw_bin = "../node-webkit-v0.10.5-osx-x64/node-webkit.app"
shutil.copytree(nw_bin, fbtmac_path)

# copy fbt_node_client to destination, app.nw mustn't already exist
contents_dir = join(fbtmac_path, 'Contents')
resources_dir = join(fbtmac_path, 'Contents', 'Resources')
release_root = join(resources_dir, 'app.nw')
shutil.copytree('fbt_node_client', release_root)  # rename fbt_node_client -> app.nw
# replace app logo
os.remove(join(resources_dir, 'nw.icns'))
shutil.copy(join('create-dmg', 'fbt.icns'), join(resources_dir, 'nw.icns'))
# replace info.plist CFBundleName
with open(join(contents_dir, 'info.plist'), 'rb') as plist:
    plist_cotent = plistload(plist)
    plist_cotent['CFBundleName'] = 'FBT'
with open(join(contents_dir, 'info.plist'), 'wb') as plist:
    plist_cotent = plistdump(plist_cotent, plist)


# remove files unnecessary files
shutil.rmtree(join(release_root, '.idea'))
os.remove(join(release_root, 'fbtLogo2.png'))
shutil.rmtree(join(release_root, 'test'))

# add readme for mac version
# with open(join('../README.txt'), 'w') as f:
#     f.write("如果运行软件时出现如下提示\nYou can’t open the application “Snagit.app” "
#             "because it may be damaged or incomplete\n")
#     f.write("请进入 菜单->系统偏好设置->安全性与隐私->通用\n")
#     f.write("允许从以下位置下载的应用程序，选择'任何来源'，就可以成功运行FBT\n")

# generate dmg
# os.chdir('create-dmg')
# Popen('./my_create_dmg.sh', shell=True)

# clean fbtmap.app
# shutil.rmtree(fbtmac_path)

