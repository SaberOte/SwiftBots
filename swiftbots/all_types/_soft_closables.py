from abc import ABC


class ISoftClosable(ABC):

    async def _soft_close_async(self) -> None:
        """
        Close all connections before shutting down an application
        """
        raise NotImplementedError()

    async def soft_close_async(self) -> None:
        """
        Close all connections (like database or http clients) before shutting down an application.
        User defined additional method.
        """
        raise NotImplementedError()
