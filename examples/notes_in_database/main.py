from swiftbots import initialize_app

from examples.notes_in_database.views.console_messaging import ConsoleView
from examples.notes_in_database.controllers.notes import Notes


def main():
    app = initialize_app()

    app.use_database("sqlite+aiosqlite:///examples/notes_in_database/database/notes.sqlite3")

    app.add_bot(ConsoleView, [Notes])

    app.run()


if __name__ == '__main__':
    main()
