import os
import inspect
from types import ModuleType
from abc import ABC
from src.botcore.bases.base_bot import BaseBot


def launch_bot(name: str):
    """
    Launches a bot by name.
    :param name: file's name in bots/ directory
    """
    check_name_valid(name)
    module = import_view(name)
    instance: BaseBot = get_class(module)()
    instance.init()
    instance.init_listen()  # Starts infinite loop and never return


def check_name_valid(name: str):
    """Check existence bot file and its correct name"""
    assert f'{name}.py' in os.listdir(f'bots'), \
        f"Module bot/{name}.py doesn't exist"
    assert not name.startswith('!'), 'bot with ! char is deactivated'


def get_class(module: ModuleType):
    for cls in inspect.getmembers(module, inspect.isclass):
        if issubclass(cls[1], BaseBot) and ABC not in cls[1].__bases__:
            return cls[1]
    raise ImportError(
        f"Can't import bot {module.__name__.split('.')[0]}. This file does not contain "
        'class that inherited from BaseBot')


def import_view(name: str) -> ModuleType:
    module = __import__(f'bots.{name}')
    instance = getattr(module, name)  # get the `name` instead of `bots.name`
    return instance
