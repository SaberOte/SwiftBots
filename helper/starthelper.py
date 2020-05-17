import os
from inspect import getsourcefile
os.chdir(os.path.abspath(getsourcefile(lambda:0))[:-21])
os.system('nohup python3 helper > ./helper/out.txt 2>&1 &')
