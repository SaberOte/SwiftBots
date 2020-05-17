if __name__ == '__main__':
    import os
    import sys
    import json
    from inspect import getsourcefile

    path = os.path.abspath(getsourcefile(lambda:0))[:-11]
    sys.path.insert(0, path+'src')
    os.chdir(path+'src')
    import botbase

    bot = botbase.BotBase()
    try:
        bot.start(1)
    except Exception as e:
        bot.sender.send(bot.keys.admin_id, 'Exception in unknown place:\n'+str(type(e))+'\n'+str(e))
