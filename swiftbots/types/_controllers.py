from abc import ABC
from typing import Callable, Optional


class IController(ABC):

    cmds: dict[str, Callable] = {}
    default: Optional[Callable] = None
