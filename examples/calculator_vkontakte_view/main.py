from swiftbots import initialize_app

from examples.calculator_vkontakte_view.views.vkontakte_view import MyVkVIew
from examples.calculator_vkontakte_view.controllers.calculator_api import CalculatorApi


def main():
    app = initialize_app()

    app.add_bot(MyVkVIew, [CalculatorApi])

    app.run()


if __name__ == '__main__':
    main()
