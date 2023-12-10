from sys import stderr

from swiftbots.types import ISysIOLogger


class SysIOLogger(ISysIOLogger):

    def info(self, *args: str | bytes) -> None:
        print(*args)

    def warn(self, *args: str | bytes) -> None:
        self.info(*args)

    def error(self, *args: str | bytes) -> None:
        print(*args, file=stderr)

    def critical(self, *args: str | bytes) -> None:
        self.error(*args)
