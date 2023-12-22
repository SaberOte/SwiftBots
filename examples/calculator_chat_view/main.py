from swiftbots import initialize_app
from swiftbots.message_handlers import BasicMessageHandler

from examples.calculator.views.console_messaging import ConsoleView
from examples.calculator.controllers.calculator_api import CalculatorApi


def main():
    app = initialize_app()

    app.add_bot(ConsoleView, [CalculatorApi], BasicMessageHandler)

    app.run()


if __name__ == '__main__':
    main()
