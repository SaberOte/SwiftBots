import os, inspect
from .templates import super_plugin
############### почему то не апдейтися. хотя все работает как надо. видимо пайтон дурак

def import_plugin(name: str) -> super_plugin.SuperPlugin:
    module = __import__(f'{__package__}.allplugins.{name}')
    instance = getattr(getattr(getattr(module,
                                       'chatbotstation'),
                               'allplugins'),
                       name)
    return instance


class PluginManager:
    plugins = []

    def __init__(self, bot):
        self._bot = bot
        self.error = bot.error
        self.log = bot.log

    def init_plugins(self):
        modules = [x[:-3] for x in os.listdir('src/chatbotstation/allplugins')
                   if x.endswith('.py')
                   and not x.startswith('__')]
        imports = []
        for x in modules:
            try:
                imports.append(import_plugin(x))
                # imports.append(__import__(f'chatbotstation.src.allplugins.{x}'))
            except Exception as e:
                self.error(f'Exception in the import module({x}):\n{str(type(e))}\n{str(e)}')
        classes = []
        for x in imports:
            for cls in inspect.getmembers(x, inspect.isclass):
                if super_plugin.SuperPlugin in cls[1].__bases__:
                    try:
                        classes.append(cls[1](self._bot))
                    except Exception as e:
                        self.error('Error in constructor plugin: ' + str(cls[0]) + '\n' + str(e))
                    break
        self.plugins = classes
        self.log(f'Loaded plugins: {str([x.__class__.__name__ for x in classes])}')

    def update_plugin(self, plugin: str) -> int:
        module = [x[:-3] for x in os.listdir('src/chatbotstation/allplugins') if x == f'{plugin}.py']
        if len(module) == 0:
            return 0
        module = module[0]
        try:
            imported = import_plugin(module)
        except Exception as e:
            raise Exception(f'Exception in the import module ({module}):\n{str(type(e))}\n{str(e)}')
        entity = None
        for cls in inspect.getmembers(imported, inspect.isclass):
            if super_plugin.SuperPlugin in cls[1].__bases__:
                try:
                    entity = cls[1](self._bot)
                except Exception as e:
                    raise Exception('Error in constructor plugin: ' + str(cls[0]) + '\n' + str(e))
                break
        if entity is None:
            raise ModuleNotFoundError(f'Plugin {module} has no class inheriting SuperPlugin')
        print(self.plugins)
        self.plugins = list(filter(lambda plg: plg.__class__.__name__ != entity.__class__.__name__, self.plugins))
        print(self.plugins)
        self.plugins.append(entity)
        print(self.plugins)
        self.log(f'Updated plugin {entity.__class__.__name__}')
        return 1
