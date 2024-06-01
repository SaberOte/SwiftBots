from abc import ABC, abstractmethod
from collections.abc import Callable, Coroutine
from typing import TYPE_CHECKING, Optional

from sqlalchemy.ext.asyncio import async_sessionmaker
from sqlalchemy.ext.asyncio.session import AsyncSession

from swiftbots.all_types import (
    IAsyncHttpClientProvider,
    IDatabaseConnectionProvider,
    ISoftClosable,
)

if TYPE_CHECKING:
    from swiftbots.all_types import IContext, IView


controller_method_type = Callable[['IView', 'IContext'], Coroutine[None, None, None]]


class IController(
    IDatabaseConnectionProvider, IAsyncHttpClientProvider, ISoftClosable, ABC
):
    cmds: dict[str, Callable] = {}
    default: Optional[Callable] = None

    @abstractmethod
    def init(self, db_session_maker: Optional[async_sessionmaker[AsyncSession]]) -> None:
        """
        Initialize all controller attributes
        """
        raise NotImplementedError()
