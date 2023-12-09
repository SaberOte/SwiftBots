"""The simplest demonstration how controller may work"""
from swiftbots.controllers import Controller


class CalculatorApi(Controller):

    def add(self, view, context: dict):
        """Add two numbers"""
        message = context['arguments']
        self.log(f'User is requesting ADD operation: {message}')
        num1, num2 = message.split(' ')
        result = float(num1) + float(num2)
        view.send(result)

    def subtract(self, view, context: dict):
        """Subtract two numbers"""
        message = context['message']
        self.log(f'User is requesting SUBTRACT operation: {message}')
        num1, num2 = message.split(' ')
        result = float(num1) - float(num2)
        view.send(result)

    cmds = {
        'add': add,
        'sub': subtract
    }
