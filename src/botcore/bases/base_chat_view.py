from sys import stderr
from src.botcore.bases.base_view import BaseView
from abc import abstractmethod


class ChatViewContext:
    def __init__(self, message: str, sender: str):
        self.message = message
        self.sender = sender


class BaseChatView(BaseView):
    admin: str
    error_message = 'Error occurred'
    unknown_error_message = 'Unknown command'
    refuse_message = 'Access forbidden'
    exit_message = 'View exited.'

    @abstractmethod
    def send(self, message, user_id):
        raise NotImplementedError(f'Not implemented method `send` in {self.name}')

    def report(self, message: str):
        """
        Send important message to admin
        :param message: report message
        """
        if self.admin is None:
            raise NotImplementedError()
        print(f'Reported "{message}"')
        return self.send(message, self.admin)

    def error(self, admin_message: str, context: ChatViewContext):
        """
        Inform user there is internal error. Admin is notifying too!
        :param admin_message: message is only for admin!!! User looks at default message
        :param context: context with `sender` and `messages` fields
        """
        try:
            if context.sender != self.admin:
                self.answer(self.error_message, context)
        finally:
            stderr.write(str(admin_message))
            return self.report(str(admin_message))

    def answer(self, message: str, context: ChatViewContext):
        """
        Text message to user
        :param message: text message
        :param context: context with `sender` and `messages` fields
        """
        sender = context.sender
        print(f'''Answered "{sender}":\n"{message}"''')
        return self.send(message, sender)

    def unknown_command(self, context: ChatViewContext):
        """
        If user sends some unknown shit, then say him about that
        :param context: context with `sender` and `messages` fields
        """
        print('Unknown command. Context:\n', context)
        return self.answer(self.unknown_error_message, context)

    def refuse(self, context: ChatViewContext):
        """
        If user can't use it, then he must be aware
        :param context: context with `sender` and `messages` fields
        """
        print(f'Forbidden. Context:\n{context}')
        return self.answer(self.refuse_message, context)
