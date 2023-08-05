import os
import inspect
import importlib
from abc import ABC
from types import ModuleType
from .bases import base_controller


def import_controller(name: str) -> ModuleType:
    module = __import__(f'controllers.{name}')
    instance = getattr(module, name)
    return instance


class ControllerManager:
    controllers = []

    def __init__(self, bot):
        self._bot = bot
        self.error = bot.error

    # init_controllers and update_controller are almost the same. Fix it!!!!!!!
    def init_controllers(self):
        modules = [x[:-3] for x in os.listdir('controllers')
                   if x.endswith('.py')
                   and not x.startswith('!')]
        imports = []
        for x in modules:
            try:
                imports.append(import_controller(x))
            except Exception as e:
                self.error(f'Exception in the import module({x}):\n{str(type(e))}\n{str(e)}')
        classes = []
        for x in imports:
            for cls in inspect.getmembers(x, inspect.isclass):
                if issubclass(cls[1], base_controller.BaseController) and ABC not in cls[1].__bases__:
                    try:
                        classes.append(cls[1](self._bot))
                    except Exception as e:
                        self.error('Error in constructor controller: ' + str(cls[0]) + '\n' + str(e))
                    break
        self.controllers = classes
        print(f'Loaded controllers: {str([x.__class__.__name__ for x in classes])}')

    def update_controller(self, controller: str) -> int:
        module = [x[:-3] for x in os.listdir('controllers') if x == f'{controller}.py']
        if len(module) == 0:
            return 0
        module = module[0]
        try:
            imported = import_controller(module)
            imported = importlib.reload(imported)
        except Exception as e:
            raise Exception(f'Exception in the import module ({module}):\n{str(type(e))}\n{str(e)}')
        entity = None
        for cls in inspect.getmembers(imported, inspect.isclass):
            if issubclass(cls[1], base_controller.BaseController) and ABC not in cls[1].__bases__:
                try:
                    entity = cls[1](self._bot)
                except Exception as e:
                    raise Exception('Error in constructor controller: ' + str(cls[0]) + '\n' + str(e))
                break
        if entity is None:
            raise ModuleNotFoundError(f'Controller {module} has no class inheriting BaseController')
        self.controllers = list(filter(lambda plg: plg.__class__.__name__ != entity.__class__.__name__, self.controllers))
        self.controllers.append(entity)
        print(f'Updated controller {entity.__class__.__name__}')
        return 1
