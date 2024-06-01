# noinspection DuplicatedCode
import os

from examples.admin_bot.controllers.admin_controller import AdminApi
from examples.admin_bot.controllers.calculator_api import CalculatorApi
from examples.admin_bot.views.admin_view import AdminView
from examples.admin_bot.views.console_messaging import ConsoleView
from swiftbots import SwiftBots
from swiftbots.admin_utils import (
    send_telegram_message,
    send_telegram_message_async,
)
from swiftbots.loggers import AdminLoggerFactory


def configure_admin_logger_factory():
    token = os.environ.get('TEST_TG_TOKEN')
    admin = os.environ.get('TG_ADMIN')
    assert token, 'Missing environment variable "TEST_TG_TOKEN"'
    assert admin, 'Missing environment variable "ADMIN_TG_TOKEN"'

    def report_func(msg):
        send_telegram_message(msg, admin, token)

    async def report_async_func(msg):
        await send_telegram_message_async(msg, admin, token)

    return AdminLoggerFactory(report_func, report_async_func)


def main():
    app = SwiftBots(logger_factory=configure_admin_logger_factory())

    app.add_bot(AdminView, [AdminApi], name='Adminer')
    app.add_bot(ConsoleView, [CalculatorApi], name='Calculator')

    app.run()


if __name__ == '__main__':
    main()
