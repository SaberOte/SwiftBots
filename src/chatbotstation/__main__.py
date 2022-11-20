"""Script's processing commands and flags"""
import os
import sys
from . import core


def main():
    """entry point"""
    set_working_dir()
    argv = sys.argv[1:]  # skip this file's name
    keys = list(filter(lambda arg: arg.startswith('-'), argv))
    args = list(filter(lambda arg: not arg.startswith('-') and not arg.startswith('{'), argv))
    flags = list(read_flags(keys))
    process_arguments(args, flags)
    sys.exit(0)


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
        yield 'debug'
    if '-MS' in keys:
        yield 'machine_start'
    if '-FR' in keys:
        yield 'from_reboot'


def process_arguments(args: list[str], flags: list[str]):
    """get arguments in order and process (not necessarily each)"""
    res_path = os.path.join(os.getcwd(), 'resources')
    if not os.path.isdir(res_path):
        os.makedirs(res_path)
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
                view = args[i]
                path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'allviews')
                os.chdir(path)
                dirs = os.listdir()
                if view not in dirs:
                    print(f'No {view} in view folder')
                    sys.exit(1)
                os.system(f'nohup python3 -m {view} > '
                          f'{res_path}/{view}_log.txt 2>&1 &')
                sys.exit(0)
            else:  # start only bot instance
                core.launch_bot(flags)
        i += 1


if __name__ != '__main__':
    main()
