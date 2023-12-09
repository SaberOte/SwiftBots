from sys import stderr

from swiftbots.types import LoggerInterface


class StandardLogger(LoggerInterface):
    """
    Logger that will log all messages to stdout or stderr
    """

    def log(self, *args: str | bytes) -> None:
        """Log to stdout"""
        print(*args)

    def error(self, *args: str | bytes) -> None:
        """Log to stderr"""
        print(*args, file=stderr)

    def critical(self, *args: str | bytes) -> None:
        """Log to stderr"""
        self.error(*args)
