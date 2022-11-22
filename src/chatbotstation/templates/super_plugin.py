from typing import Callable, Optional
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from ..core import Core


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
    def __init__(self):
        pass
    '''
    '''
    def __init__(self, bot):
    self._bot = bot
    vars_v = vars(bot)
    for var in vars_v:
        if not var.startswith('_'):
            vars(self).update({var: vars_v.get(var)})

    '''
