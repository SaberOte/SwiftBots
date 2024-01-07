import datetime as dt
from abc import ABC, abstractmethod

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from swiftbots.types import ILogger
from swiftbots.database_connection_providers import AbstractDatabaseConnectionProvider


class ITask(AbstractDatabaseConnectionProvider, ABC):
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

    @property
    @abstractmethod
    def logger(self) -> ILogger:
        raise NotImplementedError()

    @property
    @abstractmethod
    def async_db_session_maker(self) -> async_sessionmaker[AsyncSession]:
        """
        Receive one async Database session to make transactions.
        Using is like:
        ```
        async with self.async_db_session_maker() as session:
            session.add(some_other_object)
            session.commit()
        ```
        Must be used in only one asyncio task or thread.
        """
        raise NotImplementedError()

    async def soft_close_async(self) -> None:
        """
        Close all connections softly before shutting down an application
        """
        raise NotImplementedError()
