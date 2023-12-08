"""Script is processing commands and flags"""
import os
import sys
from dotenv import load_dotenv
from sys import stderr
from src.swiftbots import bots


def main():
    """entry point"""
    load_dotenv()  # .env file should only be used at development stage
    if os.getenv('ENVIRONMENT') == 'container':
        start_bot()
    raise NotImplementedError('Not implemented host stand yet')
    sys_args = sys.argv[1:]
    keys = list(filter(lambda arg: arg.startswith('-'), sys_args))
    args = list(filter(lambda arg: not arg.startswith('-') and not arg.startswith('@'), sys_args))
    flags = read_flags(keys)
    process_arguments(args, flags)


def write_reference():
    """write to stdout help information"""
    print('''Usage: python3 main.py [flags] [arguments]
Arguments:
add view: create new view and choose some template
add controller: create new controller and choose some template

Flags:
-h, --help:\nwrite this help reference
''')


def read_flags(keys: list[str]) -> list[str]:
    """pull out flags from keys"""
    flags = []
    for key in keys:
        if key in ['-h', '--help']:
            write_reference()
            sys.exit(0)
        else:
            print(f'No such key {key}')
            write_reference()
            sys.exit(1)
    return flags


def start_bot():
    name = os.getenv('BOT_NAME')
    if name.endswith('.py'):
        name = name[-3:]
    if name is None:
        print('It\'s no BOT_NAME in environment variables', file=stderr)
        sys.exit(1)
    bots.launch_bot(name)


def create_entity():
    """
    1. Ask user what to add: view or controller
    2. Ask which template to choose from src.swiftbots.view_templates or ctrl_templates
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
    path = f'src/swiftbots/{view_or_controller}_templates/'
    found_entities = os.listdir(path)
    found_entities = list(filter(lambda x: x.endswith('.py') and not x.startswith('!'), found_entities))
    entity = ''
    if len(found_entities) == 0:
        print(f"There is no {view_or_controller} in src/swiftbots/{view_or_controller}_templates/ directory!")
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
    if arg == 'add' or arg == 'create':
        create_entity()
    else:
        print(f'Argument {arg} is not recognized')
