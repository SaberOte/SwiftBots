from examples.bot_with_tasks.basic_controller import (
    BasicController,
)
from examples.bot_with_tasks.basic_view import SimpleView
from swiftbots import SwiftBots


def main():
    app = SwiftBots()

    app.add_bot(SimpleView, [BasicController])

    app.run()


if __name__ == '__main__':
    main()
