from abc import ABC

from swiftbots.types import ISoftClosable


class AbstractSoftClosable(ISoftClosable, ABC):

    async def _soft_close_async(self) -> None:
        """
        Close all connections before shutting down an application
        """
        await self.soft_close_async()

    async def soft_close_async(self) -> None:
        """
        Close all connections (like database or http clients) before shutting down an application.
        User defined additional method.
        """
        pass
