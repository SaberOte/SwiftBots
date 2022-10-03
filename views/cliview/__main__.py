import os, sys, inspect

path = os.path.dirname(os.path.abspath(__file__))
os.chdir(path)
sys.path.insert(0, os.path.join(path, '../../src'))
sys.path.insert(0, os.path.join(path, '../../templates'))
sys.path.insert(0, os.path.join(path, '.'))
from superview import SuperView


def send_ex(e, place):
    from communicator import Communicator
    import logger
    log = logger.Logger('-d' in sys.argv, './logs/').log
    comm = Communicator(__file__[:-3], log)
    log('It is a bad try to launch the view')
    msg = f'Исключение в {place}:\n' + str(type(e)) + '\n' + str(e)
    comm.send('VIEWERROR'+msg, 'core')
    log(msg)
    comm.close()


modules = [x[:-3] for x in os.listdir('.') if x.endswith('.py') and not x.startswith('_')]
imports = []
for x in modules:
    try:
        imports.append(__import__(x))
    except Exception as e:
        send_ex(e, 'import modules')
        exit(1)
all_classes = []
for x in imports:
    for cls in inspect.getmembers(x, inspect.isclass):
        if SuperView in cls[1].__bases__:
            all_classes.append(cls[1])
classes = []
for x in all_classes:
    if x not in classes:
        classes.append(x)
if len(classes) != 1:
    msg = f'This folder contains {len(classes)} classes that inherits with SuperApp, but ' \
          f'it must be unique in this folder'
    send_ex(Exception(msg), 'main')
    exit(1)
try:
    ins = classes[0]()
except Exception as e:
    send_ex(e, 'initialization')
    exit(1)
try:
    ins.init_listen()
except Exception as e:
    send_ex(e, 'executing')
    exit(1)
