import os


fullpath = os.path.abspath(__file__)
app = fullpath.split('/')[-1]
fold = fullpath.split('/')[-2]
path = fullpath[:-(len(fold)+len(app)+2)]
os.chdir(path)
os.system('nohup python3 {} > ./{}/resources/launchlogs.txt 2>&1 &'.format(fold, fold))
