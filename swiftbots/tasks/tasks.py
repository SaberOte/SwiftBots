__all__ = [
    'task',
    'TaskInfo'
]

import random
import string
from collections.abc import Callable
from typing import List, Optional, Union

from swiftbots.all_types import ITrigger
from swiftbots.types import DecoratedCallable


class TaskInfo:
    def __init__(self,
                 name: str,
                 func: DecoratedCallable,
                 triggers: List[ITrigger],
                 run_at_start: bool):
        self.name = name
        self.func = func
        self.triggers = triggers
        self.run_at_start = run_at_start


def task(
    triggers: Union[ITrigger, List[ITrigger]],
    run_at_start: bool = False,
    name: Optional[str] = None
) -> Callable[[DecoratedCallable], TaskInfo]:
    """
    Mark a bot method as a task.
    Will be executed by SwiftBots automatically.
    """
    assert isinstance(triggers, ITrigger) or isinstance(triggers, list), \
        'Trigger must be the type of ITrigger or a list of ITriggers'

    if isinstance(triggers, list):
        for trigger in triggers:
            assert isinstance(trigger, ITrigger), 'Triggers must be the type of ITrigger'
    assert isinstance(triggers, ITrigger) or len(triggers) > 0, 'Empty list of triggers'
    if name is None:
        name = str(''.join(random.choices(string.ascii_lowercase + string.digits, k=7)))
    assert isinstance(name, str), 'Name must be a string'

    def wrapper(func: DecoratedCallable) -> TaskInfo:
        task_info = TaskInfo(name=name,
                             func=func,
                             triggers=triggers if isinstance(triggers, list) else [triggers],
                             run_at_start=run_at_start)
        return task_info
    return wrapper
