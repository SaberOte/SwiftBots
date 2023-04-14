from datetime import datetime, timedelta
import os


def get_logs_path(module_name: str) -> str:
    """obtain directory path with project logs"""
    path = os.path.join(os.getcwd(), 'logs', module_name)
    if not os.path.isdir(path):
        os.makedirs(path)
    return path


class Logger:
    def __init__(self, module_name: str, is_debug: bool = False):
        self.is_debug = is_debug
        log_path = get_logs_path(module_name)
        start_time = (datetime.utcnow() + timedelta(hours=5)).strftime('%Y_%m_%d__%H_%M_%S')
        file_path = os.path.join(log_path, f'logs_{start_time}.txt')
        self.file = open(file_path, 'w', encoding='utf-8')

    def log(self, *args):
        assert len(args) > 0, 'No logs passed'
        logs = (str(log) for log in args)
        log = ' '.join(logs)
        time = (datetime.utcnow() + timedelta(hours=5)).strftime('%Y.%m.%d  %H:%M:%S')
        self.file.write(f'{time}:\t{log}\n')
        self.file.flush()
        if self.is_debug:
            print(log)
