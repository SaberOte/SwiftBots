import os
from inspect import getsourcefile
from sys import platform
fullpath = os.path.abspath(getsourcefile(lambda:0))
if platform == 'linux':
    app = fullpath.split('/')[-1]
    fold = fullpath.split('/')[-2]
elif platform == 'win32':
    app = fullpath.split('\\')[-1]
    fold = fullpath.split('\\')[-2]
else:
    print('Your system is not supported')
    exit(0)
path = fullpath[:-(len(fold)+len(app)+2)]
os.chdir(path)
if platform == 'linux':
    os.system('nohup python3 {} > ./{}/resources/logs.txt 2>&1 &'.format(fold, fold))
else:
    os.system('python {} > .\\{}\\resources\\logs.txt 2>&1'.format(fold, fold))
