from collections.abc import Callable
from typing import Annotated, Any, TypeVar

DecoratedCallable = TypeVar("DecoratedCallable", bound=Callable[..., Any])
AnnotatedType = type(Annotated[..., ...])
