"""
context must contain 'sender' and 'message' keys
"""
from src.botcore.bases.base_view import BaseView
from abc import abstractmethod


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
        self.log(f'Reported "{message}"')
        return self.send(message, self.admin)

    def error(self, message: str, context: dict):
        """
        Inform user there is internal error. Admin is notifying too.
        :param message: message is only for admin. User's looking at default message
        :param context: needs to have 'sender' property
        """
        try:
            if context['sender'] != self.admin:
                self.reply(self.error_message, context)
            self.log('ERROR\n' + str(message))
        finally:
            return self.report(str(message))

    def reply(self, message: str, context: dict):
        """
        Answer the sender
        :param message: text message
        :param context: needs to have 'sender' property
        """
        assert 'sender' in context, 'Needs "sender" defined in context!'
        sender = context['sender']
        self.log(f'''Replied "{sender}":\n"{message}"''')
        return self.send(message, sender)

    def unknown_command(self, context: dict):
        """
        If user sends some unknown shit, then say him about it
        :param context: needs to have 'sender' property
        """
        self.log('Unknown command. Context:\n', context)
        return self.reply(self.unknown_error_message, context)

    def refuse(self, context: dict):
        """
        If user can't use it, then he must be aware
        :param context: needs to have 'sender' property
        """
        self.log(f'Forbidden. Context:\n{context}')
        return self.reply(self.refuse_message, context)
