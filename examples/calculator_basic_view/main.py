from examples.calculator_basic_view.controllers.calculator_api import (
    CalculatorApi,
)
from examples.calculator_basic_view.views.console_messaging import ConsoleView
from swiftbots import initialize_app


def main():
    app = initialize_app()

    app.add_bot(ConsoleView, [CalculatorApi])

    app.run()


if __name__ == '__main__':
    main()
