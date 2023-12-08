from src.swiftbots.bases.base_view import BaseView


class ViewName(BaseView):
    def listen(self):
        """
        Input pipe for commands from user.
        Method must use "yield" operator to give information and command
        Example: yield {'command': command, 'meta': details}
        """
        raise NotImplementedError(f'Not implemented method `listen` in {self.name}')