from swiftbots.all_types import ITrigger
from swiftbots.types import DecoratedCallable


class TaskInfo:
    def __init__(self,
                 name: str,
                 func: DecoratedCallable,
                 triggers: list[ITrigger],
                 run_at_start: bool):
        self.name = name
        self.func = func
        self.triggers = triggers
        self.run_at_start = run_at_start
