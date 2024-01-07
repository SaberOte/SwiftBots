from abc import ABC, abstractmethod
from collections.abc import Callable

from sqlalchemy.ext.asyncio import async_sessionmaker
from sqlalchemy.ext.asyncio.session import AsyncSession

from swiftbots.types import IAsyncHttpClientProvider, IDatabaseConnectionProvider, ISoftClosable


class IController(IDatabaseConnectionProvider, IAsyncHttpClientProvider, ISoftClosable, ABC):

    cmds: dict[str, Callable] = {}
    default: Callable | None = None

    @abstractmethod
    def init(self, db_session_maker: async_sessionmaker[AsyncSession] | None) -> None:
        """
        Initialize all controller attributes
        """
        raise NotImplementedError()
