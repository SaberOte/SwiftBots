import superview
class CliView(superview.SuperView):
  def __init__(self, bot):
    super().__init__(bot)

  def report(self, message):
    print(message)

  def listen(self):
    yield input('->')
