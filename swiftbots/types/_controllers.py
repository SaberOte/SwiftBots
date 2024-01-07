from abc import ABC, abstractmethod
from collections.abc import Callable

from sqlalchemy.ext.asyncio import async_sessionmaker
from sqlalchemy.ext.asyncio.session import AsyncSession

from swiftbots.database_connection_providers import AbstractDatabaseConnectionProvider


class IController(AbstractDatabaseConnectionProvider, ABC):

    cmds: dict[str, Callable] = {}
    default: None or Callable = None

    @abstractmethod
    def init(self, db_session_maker: async_sessionmaker[AsyncSession] | None) -> None:
        """
        Initialize all controller attributes
        """
        raise NotImplementedError()

    async def _soft_close_async(self) -> None:
        """
        Close all connections softly before shutting down an application
        """
        raise NotImplementedError()
