from examples.notes_in_database.controllers.notes import Notes
from examples.notes_in_database.views.console_messaging import ConsoleView
from swiftbots import initialize_app


def main():
    app = initialize_app()

    app.use_database("sqlite+aiosqlite:///examples/notes_in_database/database/notes.sqlite3")

    app.add_bot(ConsoleView, [Notes])

    app.run()


if __name__ == '__main__':
    main()
