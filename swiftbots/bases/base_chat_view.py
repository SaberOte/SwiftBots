from sys import stderr
from abc import abstractmethod
from swiftbots import BaseView, ViewContext


class ChatViewContext(ViewContext):
    """
    FIELDS:
    sender: str
    message: str
    """
    def __init__(self, message: str, sender: str):
        super().__init__(message)
        self.sender = sender


class BaseChatView(BaseView):
    """
    General chat purposes view. Must LISTEN many users and ANSWER them
    """
    admin: str
    error_message = 'Error occurred'
    unknown_error_message = 'Unknown command'
    refuse_message = 'Access forbidden'
    exit_message = 'View exited.'

    @abstractmethod
    async def send(self, message, user_id):
        raise NotImplementedError(f"Not implemented method `send` in {self.get_name()}")

    @abstractmethod
    async def listen(self) -> ChatViewContext:
        """
        Input pipe for commands from user.
        Method must use "yield" operator to give information and command
        """
        raise NotImplementedError(f"Not implemented method `listen` in {self.get_name()}")

    def get_listeners(self) -> dict:
        """
        Returns an only listener. If it's needed more, then have to override this method.
        :return: set of listeners like this: {
            'whatsapp1': self.listen_WA1,
            'whatsapp2': self.listen_WA2,
            'viber': self.listen_viber
        }
        """
        return {f"{self.get_name()}_listener": self.listen}

    async def report(self, message: str):
        """
        Send important message to admin
        :param message: report message
        """
        if self.admin is None:
            raise NotImplementedError()
        print(f'Reported "{message}"')
        return await self.send(message, self.admin)

    async def error(self, admin_message: str, context: ChatViewContext):
        """
        Inform user there is internal error. Admin is notifying too!
        :param admin_message: message is only for admin!!! User looks at default message
        :param context: context with `sender` and `messages` fields
        """
        try:
            if context.sender != self.admin:
                await self.answer(self.error_message, context)
        finally:
            print(admin_message, file=stderr)
            return await self.report(str(admin_message))

    async def answer(self, message: str, context: ChatViewContext):
        """
        Text message to user
        :param message: text message
        :param context: context with `sender` and `messages` fields
        """
        sender = context.sender
        print(f'''Answered "{sender}":\n"{message}"''')
        return await self.send(message, sender)

    async def unknown_command(self, context: ChatViewContext):
        """
        If user sends some unknown shit, then needed say him about that
        :param context: context with `sender` and `messages` fields
        """
        print('Unknown command. Context:\n', context)
        return await self.answer(self.unknown_error_message, context)

    def refuse(self, context: ChatViewContext):
        """
        If user can't use it, then he must be aware.
        :param context: context with `sender` and `messages` fields
        """
        print(f'Forbidden. Context:\n{context}')
        return self.answer(self.refuse_message, context)
