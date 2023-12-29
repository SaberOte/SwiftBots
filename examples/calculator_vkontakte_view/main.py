import os

from swiftbots import initialize_app
from swiftbots.admin_utils import send_vk_message, send_vk_message_async
from swiftbots.loggers import AdminLoggerFactory

from examples.calculator_vkontakte_view.views.vkontakte_view import MyVkVIew
from examples.calculator_vkontakte_view.controllers.calculator_api import CalculatorApi


def configure_admin_logger_factory():
    token = os.environ.get('VK_TOKEN')
    admin = os.environ.get('VK_ADMIN_ID')
    assert token, f'Missing environment variable "VK_TOKEN"'
    assert admin, f'Missing environment variable "VK_ADMIN_ID"'

    def report_func(msg):
        send_vk_message(msg, admin, token)

    async def report_async_func(msg):
        await send_vk_message_async(msg, admin, token)

    return AdminLoggerFactory(report_func, report_async_func)


def main():
    app = initialize_app()

    logger_factory = configure_admin_logger_factory()
    app.use_logger(logger_factory)

    app.add_bot(MyVkVIew, [CalculatorApi], name='Awesome VK Bot')

    app.run()


if __name__ == '__main__':
    main()
