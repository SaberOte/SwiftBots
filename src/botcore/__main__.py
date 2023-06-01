"""Script is processing commands and flags"""
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


def create_entity():
    """
    1. Ask user what to add: view or controller
    2. Ask which template to choose from src.botcore.view_templates or ctrl_templates
    3. Ask how to name the file
    4. Check for similar names of existing files
    5. Move and rename file
    """
    # step 1. Choose view or controller to create
    while 1:
        view_or_controller = input('\nChoose entity to add:\n' +
                                   '1. View\n' +
                                   '2. Controller\n' +
                                   '--> ')
        if view_or_controller.lower() in ('view', '1'):
            view_or_controller = 'view'
            break
        elif view_or_controller.lower() in ('controller', '2'):
            view_or_controller = 'controller'
            break

    # step 2. Choice which exactly entity to copy
    path = f'src/botcore/{view_or_controller}_templates/'
    found_entities = os.listdir(path)
    found_entities = list(filter(lambda x: x.endswith('.py') and not x.startswith('!'), found_entities))
    entity = ''
    if len(found_entities) == 0:
        print(f"There is no {view_or_controller} in src/botcore/{view_or_controller}_templates/ directory!")
        sys.exit(1)
    elif len(found_entities) == 1:
        entity = found_entities[0]
    else:
        refactored_entities = list(map(lambda x: x[:-3].replace('_', ' ').title(), found_entities))
        listed_entities = [f'{i+1}. {x}\n' for i, x in enumerate(refactored_entities)]
        while 1:
            choice = input(f'\nChoose which {view_or_controller} exactly to add:\n' +
                           ''.join(listed_entities) +
                           '--> ')
            if not choice.isnumeric():
                choice = choice.lower().capitalize()
                try:
                    index = refactored_entities.index(choice)
                except ValueError:
                    continue
                choice = index + 1
            try:
                entity = found_entities[int(choice) - 1]
                break
            except IndexError:
                continue

    # step 3. Ask the file name
    filename = input(f'Input name for {view_or_controller}. \n'
                     f'It must be unique!\n'
                     f'Had better to end name with "{view_or_controller}"\n'
                     '--> ')
    filename = filename.lower().replace(' ', '_')
    if not filename.endswith('.py'):
        filename += '.py'
    # закончил здесь. нужно скопировать файл




def process_arguments(args: list[str], flags: list[str]):
    """get arguments in order and process"""
    args_len = len(args)
    if args_len < 1:
        print('No arguments')
        sys.exit(0)
    arg = args[0]
    if arg == 'start':
        start_view(args[1:], flags)
    elif arg == 'add' or arg == 'create':
        create_entity()
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
