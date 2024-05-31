from examples.calculator_chat_view.calculator_api import (
    CalculatorApi,
)
from examples.calculator_chat_view.console_messaging import ConsoleView
from swiftbots import SwiftBots


def main():
    app = SwiftBots()

    app.add_bot(ConsoleView, [CalculatorApi])

    app.run()


if __name__ == '__main__':
    main()
