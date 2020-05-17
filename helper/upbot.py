import os
from inspect import getsourcefile
os.chdir(os.path.abspath(getsourcefile(lambda:0))[:-33])
os.system('nohup python3 personal_manager > ./personal_manager/resources/logs.txt 2>&1 &')
