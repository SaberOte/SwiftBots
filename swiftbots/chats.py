from typing import Union

from swiftbots.all_types import ILogger
from swiftbots.types import AsyncSenderFunction


class Chat:
    error_message = "Error occurred"
    unknown_error_message = "Unknown command"
    refuse_message = "Access forbidden"

    def __init__(
            self,
            sender: Union[str, int],
            message: str,
            function_sender: AsyncSenderFunction,
            logger: ILogger
    ):
        self.sender = sender
        self.message = message
        self.function_sender = function_sender
        self.logger = logger

    async def reply_async(self, message: str) -> dict:
        return await self.function_sender(message, self.sender)

    async def error_async(self) -> dict:
        """
        Inform user there is internal error.
        """
        await self.logger.error_async(f"Error in the bot. The sender: {self.sender}, the message: {self.message}")
        return await self.reply_async(self.error_message)

    async def unknown_command_async(self) -> dict:
        """
        if a user sends some unknown shit, then needed say him about that
        """
        await self.logger.info_async(f"{self.sender} sent unknown command. {self.message}")
        return await self.reply_async(self.unknown_error_message)

    async def refuse_async(self) -> dict:
        """
        if the user can't use it, then they must be aware.
        """
        await self.logger.info_async(f"Forbidden. The sender: {self.sender}, the message: {self.message}")
        return await self.reply_async(self.refuse_message)
