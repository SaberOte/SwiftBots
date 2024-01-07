import datetime as dt
from abc import ABC, abstractmethod

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from swiftbots.all_types import (
    IAsyncHttpClientProvider,
    IDatabaseConnectionProvider,
    ILogger,
    ILoggerProvider,
    ISoftClosable,
)


class ITask(IDatabaseConnectionProvider, ILoggerProvider, IAsyncHttpClientProvider, ISoftClosable, ABC):
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
