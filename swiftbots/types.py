from collections.abc import Callable
from typing import Any, TypeVar

from typing_extensions import Annotated


class DependencyContainer:
    def __init__(self, dependency: Callable[..., Any]):
        self.dependency = dependency


DecoratedCallable = TypeVar("DecoratedCallable", bound=Callable[..., Any])
AnnotatedType = type(Annotated[Any, Any])
DependableParam = Annotated[Any, DependencyContainer]
