import os, sys
from inspect import getsourcefile
is_debug = False
for arg in sys.argv:
    if arg == '-d':
        is_debug = True
path = os.path.abspath(getsourcefile(lambda:0))[:-11]
sys.path.insert(0, path+'src')
sys.path.insert(0, path+'plugins')
sys.path.insert(0, path+'templates')
sys.path.insert(0, path+'views')
os.chdir(path+'src')

import botbase

bot = botbase.BotBase(is_debug)
try:
    bot._start_()
except Exception as e:
    bot.sender.send(bot.keys.admin_id, 'Exception in unknown place:\n'+str(type(e))+'\n'+str(e))
