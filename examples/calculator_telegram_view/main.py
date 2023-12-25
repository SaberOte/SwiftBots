from swiftbots import initialize_app

from examples.calculator_telegram_view.views.telegram_view import MyTgView
from examples.calculator_telegram_view.controllers.calculator_api import CalculatorApi


def main():
    app = initialize_app()

    app.add_bot(MyTgView, [CalculatorApi])

    app.run()


if __name__ == '__main__':
    main()
