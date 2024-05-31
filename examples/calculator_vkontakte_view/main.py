import os

from examples.calculator_vkontakte_view.calculator_api import (
    CalculatorApi,
)
from examples.calculator_vkontakte_view.vkontakte_view import MyVkVIew
from swiftbots import SwiftBots
from swiftbots.admin_utils import send_vk_message, send_vk_message_async
from swiftbots.loggers import AdminLoggerFactory


def configure_admin_logger_factory():
    token = os.environ.get('VK_TOKEN')
    admin = os.environ.get('VK_ADMIN_ID')
    assert token, 'Missing environment variable "VK_TOKEN"'
    assert admin, 'Missing environment variable "VK_ADMIN_ID"'

    def report_func(msg):
        send_vk_message(msg, admin, token)

    async def report_async_func(msg):
        await send_vk_message_async(msg, admin, token)

    return AdminLoggerFactory(report_func, report_async_func)


def main():
    app = SwiftBots()

    logger_factory = configure_admin_logger_factory()
    app.use_logger(logger_factory)

    app.add_bot(MyVkVIew, [CalculatorApi], name='Awesome Vk Bot')

    app.run()


if __name__ == '__main__':
    main()
