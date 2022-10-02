from superview import SuperView


class CliView(SuperView):
    def __init__(self):
        super().__init__()

    def report(self, message):
        print(message)

    def listen(self):
        while True:
            yield input('-> ')
