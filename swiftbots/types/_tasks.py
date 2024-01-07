import datetime as dt
from abc import ABC, abstractmethod

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from swiftbots.types import ILogger
from swiftbots.database_connection_providers import AbstractDatabaseConnectionProvider
from swiftbots.loggers import AbstractLoggerProvider


class ITask(AbstractDatabaseConnectionProvider, AbstractLoggerProvider, ABC):
    name: str
    enabled_at_start: bool = True

    @property
    @abstractmethod
    def interval(self) -> dt.timedelta:
        """Envoke task every `interval`"""
        pass

    @abstractmethod
    def init(self, logger: ILogger, db_session_maker: async_sessionmaker[AsyncSession] | None,
             name: str) -> None:
        """
        Initialize all task attributes
        """
        raise NotImplementedError()

    async def _soft_close_async(self) -> None:
        """
        Close all connections softly before shutting down an application
        """
        raise NotImplementedError()

    async def soft_close_async(self) -> None:
        """
        Close all connections softly before shutting down an application.
        User defined additional method
        """
        raise NotImplementedError()
