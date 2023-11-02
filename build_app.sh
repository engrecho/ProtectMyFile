#!/bin/bash
# 删除当前目录下的dist文件夹和build文件夹
rm -rf ./dist
rm -rf ./build

# 生成MAC的App
python3 setup.py py2app

# 复制dist下的ProtectFile应用到默认的应用程序目录
cp -Rf ./dist/ProtectFile.app /Applications/
