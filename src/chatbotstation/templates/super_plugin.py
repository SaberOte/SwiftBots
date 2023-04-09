from typing import Callable, Optional
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from ..core import Core


def admin_only(func):
    """Decorator. Should be with functions to prevent non admin execution"""
    def wrapper(self, view, context: dict):
        if view.authentic_style:
            if str(context['sender']) != str(view.admin):
                view.refuse(context)
            else:
                func(self, view, context)
        else:
            view.error('admin_only decorator requires authentic style for view', context)
    return wrapper


class SuperPlugin:
    prefixes: {str: Callable} = {}
    cmds: {str: Callable} = {}
    tasks: {str: (Callable, int, str)} = {}
    any: Optional[Callable] = None

    def __init__(self, bot: 'Core'):
        self.log = bot.log
        self.error = bot.error
        self.report = bot.report
        self._bot = bot

    '''
    def __init__(self, bot):
    self._bot = bot
    vars_v = vars(bot)
    for var in vars_v:
        if not var.startswith('_'):
            vars(self).update({var: vars_v.get(var)})

    '''
