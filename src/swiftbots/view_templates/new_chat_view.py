from src.swiftbots.bases.base_chat_view import BaseChatView


class ViewName(BaseChatView):
    controllers = []

    def listen(self):
        """
        Input pipe for commands from user.
        Method must use "yield" operator to give information and command
        Example: yield {'sender': user_id, 'message': command}
        `sender` is required property
        """
        raise NotImplementedError(f'Not implemented method `listen` in {self.name}')

    def send(self, message, user_id):
        raise NotImplementedError(f'Not implemented method `send` in {self.name}')
