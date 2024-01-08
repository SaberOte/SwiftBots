from abc import ABC


class IContext(dict, ABC):
    """
    Abstract Context class.
    Dict inheritance allows using the context like a regular dict,
    but provides a type hinting while using as a controller method argument type.
    """

    def __init__(self, **kwargs):
        """
        Constructor provides the interface of creating a Context like:
        `Context(message=message, sender=sender)`.
        """
        super().__init__()
        if "__annotations__" in self:
            for attr in self.__annotations__:
                assert attr in kwargs, (
                    f"Error while creating the Context object. Attribute {attr} must be provided "
                    f"in a constructor like `Context({attr}={attr}...)"
                )
        for arg_name in kwargs:
            self._add(arg_name, kwargs[arg_name])

    def _add(self, key: str, value: object) -> None:
        self[key] = value
        setattr(self, key, value)


class BasicPreContext(IContext):
    """
    One required attribute `message` of any type
    """

    message: object

    def __init__(self, message: object, **kwargs):
        super().__init__(message=message, **kwargs)


class BasicContext(IContext):
    """
    One required attribute `raw_message` of any type
    """

    raw_message: object


class ChatPreContext(IContext):
    """
    One required field:
    message - raw message from sender.
    One optional but mostly useful field:
    sender - user from whom the message was sent
    """

    message: str
    sender: str | int

    def __init__(self, message: str, sender: str | int = "unknown", **kwargs):
        super().__init__(message=message, sender=sender, **kwargs)


class ChatContext(IContext):
    """
    Four required fields:
    `raw_message` - not modified message.
    `arguments` - message with cut-out command part (empty string if not given).
    `command` - part of the message what was matched as a command.
    `sender` - user from whom the message was received.

    If `default` method was called, raw_message, command and arguments will both contain not modified message.
    """

    raw_message: str
    arguments: str
    command: str
    sender: str | int


class TelegramPreContext(ChatPreContext):
    """
    Three required fields:
    `message` - raw message from sender.
    `sender` - user from whom the message was received
    `username` - user's symbolic username: `no username` if user has no symbolic username
    """

    message: str
    sender: str
    username: str

    def __init__(self, message: str, sender: str, username: str, **kwargs):
        super().__init__(message=message, sender=sender, username=username, **kwargs)


class TelegramContext(ChatContext):
    """
    Five required fields:
    `raw_message` - not modified message.
    `arguments` - message with cut-out command part (empty string if not given).
    `command` - part of the message what was matched as a command.
    `sender` - user from whom the message was received.
    `username` - user's symbolic username. `no username` if user has no symbolic username

    If `default` method was called, raw_message, command and arguments will both contain not modified message.
    """

    raw_message: str
    arguments: str
    command: str
    sender: str
    username: str


class VkontaktePreContext(ChatPreContext):
    """
    Three required fields:
    `message` - raw message from sender.
    `sender` - user from whom the message was received.
    `message_id` - message id.
    """

    message: str
    sender: int
    message_id: int

    def __init__(self, message: str, sender: int, message_id: int, **kwargs):
        super().__init__(
            message=message, sender=sender, message_id=message_id, **kwargs
        )


class VkontakteContext(ChatContext):
    """
    Five required fields:
    `raw_message` - not modified message.
    `arguments` - message with cut-out command part (empty string if not given).
    `command` - part of the message what was matched as a command.
    `sender` - user from whom the message was received.
    `message_id` - message id.

    If `default` method was called, raw_message, command and arguments will all contain not modified message.
    """

    raw_message: str
    arguments: str
    command: str
    sender: int
    message_id: int
