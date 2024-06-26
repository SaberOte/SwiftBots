from abc import ABC, abstractmethod
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker


class IDatabaseConnectionProvider(ABC):
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
        Must be used in only one task or thread.
        """
        raise NotImplementedError()

    @abstractmethod
    def _set_db_session_maker(
        self, db_session_maker: Optional[async_sessionmaker[AsyncSession]]
    ) -> None:
        raise NotImplementedError()
