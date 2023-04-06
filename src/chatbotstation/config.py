import configparser
import os
import time


def __get_path(name: str) -> str:
    return os.path.join(os.getcwd(), 'resources', name)


def read_config(name: str):
    config = configparser.ConfigParser()
    for i in range(10):  # очень странная ошибка этой библы. иногда конфиг впустую читается. хуйня американская
        config.read(__get_path(name))
        if len(config.sections()):
            break
        print('EMPTY CONFIG!!')
        time.sleep(0.1)
    return config


def write_config(config, name: str):
    file = open(__get_path(name), 'w')
    config.write(file)
    file.close()


def fill_config_ini():
    path = __get_path('config.ini')
    if not os.path.exists(path):
        if not os.path.isdir(os.path.dirname(path)):
            os.makedirs(os.path.dirname(path))
        file = open(path, 'w')
        file.close()
    config = read_config('config.ini')
    changed = False
    if 'Disabled_Views' not in config.sections():
        config.add_section('Disabled_Views')
        changed = True
    if 'Names' not in config.sections():
        config.add_section('Names')
        changed = True
    if 'Tasks' not in config.sections():
        config.add_section('Tasks')
        changed = True
    if 'Main_View' not in config.sections():
        config.add_section('Last_Views')
        changed = True
    if 'Main_View' not in config.sections():
        config.add_section('Main_View')
        changed = True
    if changed:
        write_config(config, 'config.ini')
