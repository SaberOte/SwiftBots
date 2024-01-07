from abc import ABC, abstractmethod
import datetime as dt

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from swiftbots.types import ILogger


class ITask(ABC):

    @property
    @abstractmethod
    def interval(self) -> dt.timedelta:
        pass

    name: str = None

    @abstractmethod
    def init(self, logger: ILogger, db_session_maker: async_sessionmaker[AsyncSession] | None) -> None:
        """
        Initialize all task attributes
        """
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
        Must be used in only 1 asyncio task or thread.
        """
        raise NotImplementedError()

    async def soft_close_async(self) -> None:
        """
        Close all connections softly before shutting down an application
        """
        raise NotImplementedError()
