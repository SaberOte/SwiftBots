"""Minimal demonstration of the simple chatbot view in the terminal"""
from swiftbots.views import ChatView


class ConsoleView(ChatView):

    def listen(self):
        print("Welcome in the command line chat! Good day, Friend!")
        while True:
            message = input('-> ')
            ans = {
                'message': message,
                'sender': 'pidaras'
            }
            yield ans

    def send(self, message):
        print(message)
