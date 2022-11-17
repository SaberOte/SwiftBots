import configparser, os, time


def __getpath():
    relative_path = '../resources/config.ini'
    return os.path.join(os.path.dirname(os.path.realpath(__file__)), relative_path)


def readconfig():
    config = configparser.ConfigParser()
    for i in range(10):  # очень странная ошибка этой библы. иногда конфиг впустую читается. хуйня американская
        config.read(__getpath())
        if len(config.sections()):
            break
        print('EMPTY CONFIG!!')
        time.sleep(0.1)
    return config


def writeconfig(config):
    file = open(__getpath(), 'w')
    config.write(file)
    file.close()


def fillconfig():
    config = readconfig()
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
        writeconfig(config)
