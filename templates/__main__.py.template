import os
import sys
import inspect
path = os.path.abspath(inspect.getsourcefile(lambda:0))[:-11]
os.chdir(path)
sys.path.insert(0, path+'../../src')
sys.path.insert(0, path+'../../templates')
sys.path.insert(0, path+'.')
from superapp import SuperApp

def send_ex(e, place):
    import keys, logger, apimanager, msgsender
    loggerr = logger.Logger(True, './logs/')
    loggerr.log('It is bad try to launch app')
    keys = keys.KeyManager('./../../resources/data.json', loggerr.log)
    api = apimanager.ApiManager(keys, loggerr.log)
    sender = msgsender.Sender('./../../resources/', keys, api, loggerr.log)
    sender.report(f'Исключение в {place}:\n'+str(type(e))+'\n'+str(e))
    loggerr.log(f'Exception in the {place}:\n'+str(type(e))+'\n'+str(e))
    
modules = [x[:-3] for x in os.listdir('.') if x.endswith('.py') and not x.startswith('_')]
imports = []
for x in modules:
    try:
        imports.append(__import__(x))
    except Exception as e:
        send_ex(e, 'import modules')
all_classes = []
for x in imports:
    for cls in inspect.getmembers(x, inspect.isclass):
        if SuperApp in cls[1].__bases__:
            all_classes.append(cls[1])
classes = []
for x in all_classes:
    if x not in classes:
        classes.append(x)
if len(classes) != 1:
    msg = f'This folder contains {len(classes)} classes that inherits with SuperApp, but it must be unique in this folder'
    send_ex(Exception(msg), 'main')
    exit(1)
try:
    ins = classes[0]()
except Exception as e:
    send_ex(e, 'initialization')
ins.listen()
