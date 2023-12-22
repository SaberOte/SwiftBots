"""Minimal demonstration of the simple chatbot view in the terminal"""
from swiftbots.views import ChatView


class ConsoleView(ChatView):
    """
    It's a bad example, `print` and `input` doesn't run asynchronously,
    but it's pretty simple.
    """

    async def listen_async(self):
        print("Welcome in the command line chat! Good day, Friend!")
        while True:
            message = input('-> ')
            ans = {
                'message': message,
                'sender': 'pidaras'
            }
            yield ans

    async def send_async(self, message, context):
        print(message)
