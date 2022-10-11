import os, sys

is_debug = False
if '-d' in sys.argv:
    is_debug = True
path = os.path.dirname(os.path.abspath(__file__))
os.chdir(path)
sys.path.insert(0, os.path.join(path, 'src'))
sys.path.insert(0, os.path.join(path, 'plugins'))
sys.path.insert(0, os.path.join(path, 'templates'))
sys.path.insert(0, os.path.join(path, 'views'))
os.chdir(os.path.join(path, 'src'))

import botbase

bot = botbase.BotBase(is_debug)
try:
    bot._start_()
except Exception as e:
    msg = 'Exception in unknown place:\n'+str(type(e))+'\n'+str(e)
    if bot.error:
        bot.error(msg)
    else:
        print(msg)
