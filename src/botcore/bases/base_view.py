from abc import ABC


class ViewContext:
    """
    FIELDS:
    message: str
    """
    def __init__(self, message: str):
        self.message = message


class BaseView(ABC):
    """
    Minimal view must at least listen some outer resource and invoke bot controllers
    """
    async def listen(self) -> ViewContext:
        """
        Input pipe for commands from user.
        Method must use "yield" operator to give information and command
        """
        raise NotImplementedError(f"Not implemented method `listen` in {self.get_name()}")

    def get_listeners(self) -> dict:
        """
        By default, it returns nothing.
        If this view should receive messages from users,
        it's needed to override this method and add at least 1 listener.
        Example is src/botcore/bases/base_telegram_view.py.
        :return: set of listeners like this: {
            'whatsapp1': self.listen_WA1,
            'whatsapp2': self.listen_WA2,
            'viber': self.listen_viber
        }
        """
        return {}

    def get_name(self) -> str:
        return self.__module__.split('.')[-1]
