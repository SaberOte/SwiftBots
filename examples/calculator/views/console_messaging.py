"""Minimal demonstration of the simple chatbot view in the terminal"""
from swiftbots.types import ChatView


class ConsoleView(ChatView):

    async def alisten(self):
        print("Welcome in the command line chat! Good day, Friend!")
        while True:
            message = input('-> ')
            ans = {
                'message': message,
                'sender': 'pidaras'
            }
            yield ans

    async def asend(self, message, context):
        print(message)
