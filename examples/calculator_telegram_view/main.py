import os

from swiftbots import initialize_app
from swiftbots.admin_utils import send_telegram_message_async, send_telegram_message
from swiftbots.loggers import AdminLoggerFactory

from examples.calculator_telegram_view.views.telegram_view import MyTgView
from examples.calculator_telegram_view.controllers.calculator_api import CalculatorApi


def configure_admin_logger_factory():
    token = os.environ.get('TELEGRAM_TOKEN')
    admin = os.environ.get('TELEGRAM_ADMIN_ID')
    assert token, 'Missing environment variable "TELEGRAM_TOKEN"'
    assert admin, 'Missing environment variable "TELEGRAM_ADMIN_ID"'

    def report_func(msg):
        send_telegram_message(msg, admin, token)

    async def report_async_func(msg):
        await send_telegram_message_async(msg, admin, token)

    return AdminLoggerFactory(report_func, report_async_func)


def main():
    app = initialize_app()

    logger_factory = configure_admin_logger_factory()
    app.use_logger(logger_factory)

    app.add_bot(MyTgView, [CalculatorApi])

    app.run()


if __name__ == '__main__':
    main()
