"""Script's processing commands and flags"""
import os
import sys
import signal
from src.botcore import views


def main():
    """entry point"""
    set_working_dir()
    prepare_project()
    sys_args = sys.argv[1:]
    keys = list(filter(lambda arg: arg.startswith('-'), sys_args))
    args = list(filter(lambda arg: not arg.startswith('-') and not arg.startswith('@'), sys_args))
    flags = read_flags(keys)
    process_arguments(args, flags)


def prepare_project():
    """Create all needed directories"""
    logs_path = os.path.join(os.getcwd(), 'logs')
    if not os.path.isdir(logs_path):
        os.makedirs(logs_path)


def set_working_dir():
    """sets project root directory as a working directory"""
    # full file path's is PROJECT_PATH/src/botcore/__main__.py
    # work directory must be PROJECT_PATH/
    get_prev = os.path.dirname
    path = get_prev(get_prev(get_prev(os.path.abspath(__file__))))
    os.chdir(path)


def write_reference():
    """write to stdout help information"""
    print('''Usage: python3 main.py [arguments] [flags]
Arguments:
start `VIEW_NAME`: start certain view from ./views manually
add view: create new view and choose some template
add controller: create new controller and choose some template

Flags:
--debug\t\t-d : print every log
''')


def read_flags(keys: list[str]) -> list[str]:
    """pull out flags from keys"""
    flags = []
    for key in keys:
        if key in ['-h', '--help']:
            write_reference()
            sys.exit(0)
        elif key in ['-d', '--debug']:
            flags.append('debug')  # write logs also in stdout
        elif key in ['--ms', '--machine-start']:
            flags.append('machine start')  # app launched programmatically. So start instance directly
        elif key in ['--fr', '--from-reboot']:
            flags.append('from reboot')  # let view know it's rebooting but not initial start
        else:
            print(f'No such key {key}')
            write_reference()
            sys.exit(1)
    return flags


def start_view(args: list[str], flags: list[str]):
    if len(args) == 0:
        print('Need a view name to start!')
        write_reference()
        sys.exit(1)
    view = args[0]
    views.launch_view(view, flags)


def create_view(): # тут и закончил


def process_arguments(args: list[str], flags: list[str]):
    """get arguments in order and process"""
    args_len = len(args)
    if args_len <= 1:
        print('No arguments')
        sys.exit(0)
    arg = args[0]
    if arg == 'start':
        start_view(args[1:], flags)
    elif arg == 'add':
        create_view()
    else:
        print(f'Argument {arg} is not recognized')


def signal_usr1(signum, frame):
    """
    Calls just in BaseView when it's needed to update the current view.
    So main calls again without rebooting all program.
    Due to python features all imported modules are cached, so it force reloads only view
    """
    main()


signal.signal(signal.SIGUSR1, signal_usr1)


if __name__ != '__main__':
    main()
