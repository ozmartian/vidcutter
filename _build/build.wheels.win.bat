@echo off

cd ..
python setup.py bdist_wheel --plat-name win32
python setup.py bdist_wheel --plat-name win-amd64
