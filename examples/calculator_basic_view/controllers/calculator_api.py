"""The simplest demonstration how controller may work"""
import asyncio

from swiftbots.types import IBasicView
from swiftbots.controllers import Controller


def print_async(*args, **kwargs):
    return asyncio.to_thread(print, *args, **kwargs)


class CalculatorApi(Controller):

    async def calculate(self, view: IBasicView, context: IBasicView.Context):
        message = str(context.message)
        num1, operation, num2 = message.split(' ')
        self.info(f'User is requesting `{operation}` operation with numbers: {num1} and {num2}')
        if operation == '-':
            await print_async(f'Result is {float(num1) - float(num2)}')
        elif operation == '+':
            await print_async(f'Result is {float(num1) + float(num2)}')
        elif operation == '*':
            await print_async(f'Result is {float(num1) * float(num2)}')
        elif operation == '/':
            await print_async(f'Result is {float(num1) / float(num2)}')
        else:
            await print_async(f'Unknown operation {operation}')

    default = calculate
