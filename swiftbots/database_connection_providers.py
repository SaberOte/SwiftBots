from abc import ABC

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker


class AbstractDatabaseConnectionProvider(ABC):
    __db_session_maker: async_sessionmaker[AsyncSession] | None = None

    @property
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
        assert self.__db_session_maker, \
            "Application hasn't database engine. Call use_database for application before running"
        return self.__db_session_maker

    def _set_db_session_maker(self, db_session_maker: async_sessionmaker[AsyncSession] | None) -> None:
        self.__db_session_maker = db_session_maker
