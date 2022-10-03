import configparser, os

def __getpath():
    relative_path = '../resources/config.ini'
    return os.path.join(os.path.dirname(os.path.realpath(__file__)), relative_path)
    '''
    target_dir = 'resources/config.ini'
    delimiter = '.'
    counter = 0
    while not os.path.exists(os.path.join(delimiter, target_dir)):
        delimiter = os.path.join(delimiter, '..')
        counter += 1
        if counter > 100:
            raise Exception('Too many attempts find config path in config.py')
    return os.path.join(delimiter, target_dir)
    '''

def readconfig():
    config = configparser.ConfigParser()
    config.read(__getpath())
    return config

def writeconfig(config):
    file = open(__getpath(), 'w')
    config.write(file)
    file.close()
