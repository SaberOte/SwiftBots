from abc import ABC, abstractmethod
from typing import Callable, Optional, TYPE_CHECKING

from sqlalchemy.ext.asyncio import async_sessionmaker
from sqlalchemy.ext.asyncio.session import AsyncSession

if TYPE_CHECKING:
    from swiftbots.bots import Bot


class IController(ABC):

    cmds: dict[str, Callable] = {}
    default: Optional[Callable] = None

    @abstractmethod
    def init(self, db_session_maker: async_sessionmaker[AsyncSession]) -> None:
        """
        Initialize all controller attributes
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
        Must be used in only 1 task or thread.
        """
        raise NotImplementedError()
