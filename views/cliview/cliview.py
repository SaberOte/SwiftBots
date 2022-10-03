from superview import SuperView


class CliView(SuperView):
    def __init__(self):
        super().__init__()

    def report(self, message):
        print(message)

    def listen(self):
        print("Hello in the command line interface! Good day!")
        while True:
            yield input('-> ')
