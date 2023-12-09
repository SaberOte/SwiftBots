"""The simplest demonstration how controller may work"""
from swiftbots.types import Controller, ChatView


class CalculatorApi(Controller):

    async def add(self, view: ChatView, context: dict):
        """Add two numbers"""
        message = context['arguments']
        self.log(f'User is requesting ADD operation: {message}')
        num1, num2 = message.split(' ')
        result = float(num1) + float(num2)
        await view.asend(str(result), context)

    def subtract(self, view: ChatView, context: dict):
        """Subtract two numbers"""
        message = context['message']
        self.log(f'User is requesting SUBTRACT operation: {message}')
        num1, num2 = message.split(' ')
        result = float(num1) - float(num2)
        view.asend(str(result), context)

    cmds = {
        'add': add,
        'sub': subtract
    }
