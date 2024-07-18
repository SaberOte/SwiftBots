import random
from collections.abc import Callable
from typing import Dict, Optional, Union

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
        """
        Send the user the message back.
        """
        return await self.function_sender(message, self.sender)

    async def error_async(self) -> dict:
        """
        Inform the user there is an internal error.
        """
        await self.logger.error_async(f"Error in the bot. The sender: {self.sender}, the message: {self.message}")
        return await self.reply_async(self.error_message)

    async def unknown_command_async(self) -> dict:
        """
        If the user sends some unknown shit, then needed to warn him
        """
        await self.logger.info_async(f"{self.sender} sent unknown command. {self.message}")
        return await self.reply_async(self.unknown_error_message)

    async def refuse_async(self) -> dict:
        """
        If the user can't use it, then he must be aware.
        """
        await self.logger.info_async(f"Forbidden. The sender: {self.sender}, the message: {self.message}")
        return await self.reply_async(self.refuse_message)


class TelegramChat(Chat):
    def __init__(
            self,
            sender: Union[str, int],
            message: str,
            function_sender: AsyncSenderFunction,
            logger: ILogger,
            message_id: int,
            username: Union[str, None],
            fetch_async: Callable
    ):
        super().__init__(sender=sender,
                         message=message,
                         function_sender=function_sender,
                         logger=logger)
        self.message_id = message_id
        self.username = username
        self.fetch_async = fetch_async

    async def update_message_async(
        self, new_text: str, message_id: int, data: Optional[Dict] = None
    ) -> dict:
        if data is None:
            data = {}
        data["text"] = new_text
        data["message_id"] = message_id
        data["chat_id"] = self.sender
        return await self.fetch_async("editMessageText", data)

    async def send_async(
        self, message: str, user: Union[str, int], data: Optional[dict] = None
    ) -> dict:
        if data is None:
            data = {}

        messages = [message[i: i + 4096] for i in range(0, len(message), 4096)]
        result = {}
        for msg in messages:
            send_data = {"chat_id": user, "text": msg}
            send_data.update(data)
            result = await self.fetch_async("sendMessage", send_data)
        return result

    async def delete_message_async(
        self, message_id: int, data: Optional[dict] = None
    ) -> dict:
        if data is None:
            data = {}
        data["chat_id"] = self.sender
        data["message_id"] = message_id
        return await self.fetch_async("deleteMessage", data)

    async def send_sticker_async(
        self, file_id: str, data: Optional[dict] = None
    ) -> dict:
        if data is None:
            data = {}
        data["chat_id"] = self.sender
        data["sticker"] = file_id
        return await self.fetch_async("sendSticker", data)


class VkChat(Chat):
    def __init__(
            self,
            sender: Union[str, int],
            message: str,
            function_sender: AsyncSenderFunction,
            logger: ILogger,
            message_id: int,
            fetch_async: Callable
    ):
        super().__init__(sender=sender,
                         message=message,
                         function_sender=function_sender,
                         logger=logger)
        self.message_id = message_id
        self.fetch_async = fetch_async

    async def send_async(
        self, message: str, user: Union[int, str], data: Optional[dict] = None
    ) -> dict:
        """
        :returns: {
              "response": 5
          }, where response is a message id
        """
        if data is None:
            data = {}
        # if the message out of 4096 letters, split it on chunks
        messages = [message[i : i + 4096] for i in range(0, len(message), 4096)]
        result = {}
        for msg in messages:
            send_data = {
                "user_id": int(user),
                "message": msg,
                "random_id": random.randint(-(2 ** 31), 2 ** 31)
            }
            send_data.update(data)
            result = await self.fetch_async("messages.send", send_data)
        return result

    async def update_message_async(
        self,
        new_message: str,
        message_id: int,
        data: Optional[dict] = None,
    ) -> dict:
        if data is None:
            data = {}
        data["peer_id"] = self.sender
        data["message_id"] = message_id
        data["message"] = new_message
        return await self.fetch_async("messages.edit", data)

    async def send_sticker_async(
        self, sticker_id: int, data: Optional[dict] = None
    ) -> dict:
        if data is None:
            data = {}
        data["user_id"] = self.sender
        data["random_id"] = random.randint(-(2 ** 31), 2 ** 31)
        data["sticker_id"] = sticker_id
        return await self.fetch_async("messages.send", data)
