from sys import stderr

from swiftbots.types import ISysIOLogger


class SysIOLogger(ISysIOLogger):

    def info(self, *args, **kwargs) -> None:
        print(*args, **kwargs)

    def warn(self, *args, **kwargs) -> None:
        self.info(*args, **kwargs)

    def error(self, *args, **kwargs) -> None:
        print(*args, **kwargs, file=stderr)

    def critical(self, *args, **kwargs) -> None:
        self.error(*args, **kwargs)
