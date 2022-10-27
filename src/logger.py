from datetime import datetime, timedelta
import os


class Logger:
    def __init__(self, is_debug: bool, path: str):
        self.is_debug = is_debug
        path = path
        if not os.path.isdir(os.path.dirname(path)):
            os.makedirs(os.path.dirname(path))
        starttime = (datetime.utcnow() + timedelta(hours=5)).strftime('%Y_%m_%d__%H_%M_%S')
        self.file = open(path+'logs_'+starttime+'.txt', 'w', encoding='utf-8')
    
    def log(self, log: str):
        log = str(log)
        self.file.write(log + '\t' + (datetime.utcnow() + timedelta(hours=5)).strftime('%Y.%m.%d  %H:%M:%S') + '\n')
        self.file.flush()
        if self.is_debug:
            print(log)
