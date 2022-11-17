"""This script is an entry point to app.
Starts with commands and flags"""
import os
import sys
from traceback import format_exc
import core


def get_resources_path() -> str:
    """obtain directory path with project data"""
    # full path's smth like ~/FOLDER/src/chatbotstation/__main__.py
    # resources directory is ~/FOLDER/resources
    get_prev = os.path.dirname
    path = os.path.join(get_prev(get_prev(get_prev(os.path.abspath(__file__)))), 'resources')
    if not os.path.isdir(path):
        os.makedirs(path)
    return path


def read_flags():
    """pull out flags from flags variable"""
    if '-h' in keys or '-help' in keys or '--help' in keys:
        print('''Usage: python3 [__main__.py | FILE'S DIRECTORY] [arguments] [flags]
Arguments:
start        : start this bot
start [view] : start view manually

Flags:
-d : print every log
''')
        sys.exit(0)
    if '-d' in keys:
        yield 'debug'
    if '-MS' in keys:
        yield 'machine_start'
    if '-FR' in keys:
        yield 'from_reboot'


def process_arguments():
    """get arguments in order and process (not necessarily each)"""
    i = 0
    args_len = len(args)
    if args_len == 0:
        print('No arguments')
        sys.exit(0)
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
                    sys.exit(1)
                os.system(f'nohup python3 {view} > '
                          f'{res_path}/{view}_log.txt 2>&1 &')
            else:
                if 'debug' in flags or 'machine_start' in flags:  # explicit start
                    launch_bot()
                else:  # quite start
                    # set directory src as main and call python3 THIS_MODULE
                    fullpath = os.path.dirname(os.path.abspath(__file__))
                    proj_name = fullpath.split('/')[-1]
                    work_path = os.path.dirname(proj_name)
                    os.chdir(work_path)
                    os.system(f'nohup python3 {proj_name} start -MS > '
                              f'{res_path}/launch_log.txt 2>&1 &')
                    sys.exit(0)
        i += 1


def launch_bot():
    """start core instance"""
    bot = core.Core('debug' in flags)
    try:
        if 'from_reboot' in flags:
            bot.views_manager.report('Бот перезапущен')
    except:
        pass
    try:
        bot.start()
    except:
        msg = format_exc()
        if bot.error:
            bot.error(msg)
        else:
            print(msg)
        sys.exit(1)


if __name__ == "__main__":
    argv = sys.argv[1:]  # skip this file's name
    keys = list(filter(lambda arg: arg.startswith('-'), argv))
    args = list(filter(lambda arg: not arg.startswith('-') and not arg.startswith('{'), argv))
    res_path = get_resources_path()

    flags = list(read_flags())
    process_arguments()
    sys.exit(0)
