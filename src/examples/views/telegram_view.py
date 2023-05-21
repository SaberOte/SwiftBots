"""
This is an example of telegram view initializing
That's useless without controllers. View is only input/output model. It does not do anything
Controllers do all the tasks or commands
So it's needed to pass to `controllers` property at least one from PROJECT/controllers directory
Name of each controller must be the same as it file name (but without ".py" extension)

In the case of telegram view there are must be environment variables:
TELEGRAM_TOKEN - bot token that can be acquired from @BotFather
ADMIN_ID - telegram id of the admin or person who will receive errors or important messages
Numeric id only allowed, but not username! Can be received with bot @getmyid_bot

Class could have any name. File name is restricted only
"""
from src.botcore.templates.base_telegram_view import BaseTelegramView


class TelegramView(BaseTelegramView):
    controllers = ['say_hello']

    def __init__(self):
        self.init_credentials()
