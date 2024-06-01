from examples.notes_in_database.controllers.notes import Notes
from examples.notes_in_database.views.console_messaging import ConsoleView
from swiftbots import SwiftBots


def main():
    app = SwiftBots(db_connection_string="sqlite+aiosqlite:///examples/notes_in_database/database/notes.sqlite3")

    app.add_bot(ConsoleView, [Notes])

    app.run()


if __name__ == '__main__':
    main()
