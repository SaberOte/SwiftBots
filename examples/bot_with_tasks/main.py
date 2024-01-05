from swiftbots import initialize_app

from examples.bot_with_tasks.views.basic_view import SimpleView
from examples.bot_with_tasks.controllers.basic_controller import BasicController


def main():
    app = initialize_app()

    app.add_bot(SimpleView, [BasicController])

    app.run()


if __name__ == '__main__':
    main()
