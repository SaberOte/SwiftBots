# this script enters flags and commands and does anything
import os, sys

argv = sys.argv[1:]  # skip this file's name
flags = list(filter(lambda arg: arg.startswith('-'), argv))
args = list(filter(lambda arg: not arg.startswith('-') and not arg.startswith('{'), argv))

is_debug = False
is_machine_start = False
from_reboot = False


def process_flags():
    if '-h' in flags or '-help' in flags or '--help' in flags:
        print('''Usage: python3 [__main__.py | FILE'S DIRECTORY] [arguments] [flags]
Arguments:
start        : start this bot
start [view] : start view manually

Flags:
-d : print every log
''')
        exit()
    if '-d' in flags:
        global is_debug
        is_debug = True
    if '-MS' in flags:
        global is_machine_start
        is_machine_start = True
    if '-FR' in flags:
        global from_reboot
        from_reboot = True


def process_arguments():
    i = 0
    args_len = len(args)
    if args_len == 0:
        print('No arguments')
        exit()
    while i < args_len:
        arg = args[i]
        if arg == 'start':
            if i + 1 != args_len:
                i += 1
                view = args[i]
                path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'views')
                os.chdir(path)
                dirs = os.listdir()
                if view not in dirs:
                    print('No such view in view folder')
                    exit()
                os.system('nohup python3 {} > ./{}/logs/launchlogs.txt 2>&1 &'.format(view, view))
            else:
                if is_debug or is_machine_start:  # explicit start
                    launch_bot()
                else:  # quite start
                    fullpath = os.path.dirname(os.path.abspath(__file__))
                    fold = fullpath.split('/')[-1]
                    path = os.path.dirname(fullpath)
                    os.chdir(path)
                    os.system('nohup python3 {} start -MS > ./{}/resources/launchlogs.txt 2>&1 &'.format(fold, fold))
                    exit()

        i += 1


def launch_bot():
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
        if from_reboot:
            bot.views_manager.report('Бот перезапущен')
    except: pass
    try:
        bot._start_()
    except Exception as e:
        msg = 'Exception in unknown place:\n' + str(type(e)) + '\n' + str(e)
        if bot.error:
            bot.error(msg)
        else:
            print(msg)
        exit()


if __name__ == "__main__":
    process_flags()
    process_arguments()
    exit()

