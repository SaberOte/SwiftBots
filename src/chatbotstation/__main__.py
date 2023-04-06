"""Script's processing commands and flags"""
import os
import sys
import signal
from traceback import format_exc
from . import core
from . import views
from .config import fill_config


def main():
    """entry point"""
    try:
        set_working_dir()
        prepare_project()
        argv = sys.argv[1:]  # skip this file's name
        keys = list(filter(lambda arg: arg.startswith('-'), argv))
        args = list(filter(lambda arg: not arg.startswith('-') and not arg.startswith('@'), argv))
        flags = list(read_flags(keys))
        process_arguments(args, flags)
    except:
        print(format_exc())


def prepare_project():
    """Create all needed directories"""
    res_path = os.path.join(os.getcwd(), 'resources')
    if not os.path.isdir(res_path):
        os.makedirs(res_path)
    logs_path = os.path.join(os.getcwd(), 'logs')
    if not os.path.isdir(logs_path):
        os.makedirs(logs_path)
    fill_config('config.ini')


def set_working_dir():
    """sets project root directory as a working directory"""
    # full file path's smth like ~/FOLDER/src/chatbotstation/__main__.py
    # work directory must be ~/FOLDER/
    get_prev = os.path.dirname
    path = get_prev(get_prev(get_prev(os.path.abspath(__file__))))
    os.chdir(path)


def read_flags(keys: list[str]):
    """pull out flags from keys"""
    if '-h' in keys or '-help' in keys or '--help' in keys:
        print('''Usage: python3 main.py [arguments] [flags]
Arguments:
start        : start this bot
start [view] : start view manually

Flags:
-d : print every log
''')
        sys.exit(0)
    if '-d' in keys:
        yield 'debug'  # output debug also through print()
    if '-MS' in keys:
        yield 'machine start'  # launched programmatically. Start instance directly
    if '-FR' in keys:
        yield 'from reboot'  # send message 'restarted' to admin


def process_arguments(args: list[str], flags: list[str]):
    """get arguments in order and process (not necessarily each)"""
    i = 0
    args_len = len(args)
    if args_len == 0:
        print('No arguments')
        sys.exit(0)
    while i < args_len:
        arg = args[i]
        if arg == 'start':
            if i + 1 != args_len:  # start VIEW
                i += 1
                views.launch_view(args[i], flags)
            else:  # start only bot instance
                core.launch_bot(flags)
        else:
            print(f'Argument {arg} is not recognized')
        i += 1


def signal_usr1(signum, frame):
    """
    Calls just in SuperView when it's needed to update the current view.
    So main calls again without rebooting all program.
    Due to python features all imported modules are cached, so it force reloads only view
    """
    main()


signal.signal(signal.SIGUSR1, signal_usr1)


if __name__ != '__main__':
    main()
