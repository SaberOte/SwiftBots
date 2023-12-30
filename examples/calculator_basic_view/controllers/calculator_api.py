"""The simplest demonstration how controller may work"""
import asyncio

from swiftbots.types import IBasicView
from swiftbots.controllers import Controller


def print_async(*args, **kwargs):
    return asyncio.to_thread(print, *args, **kwargs)


class CalculatorApi(Controller):

    async def calculate(self, view: IBasicView, context: IBasicView.Context):
        message = str(context.raw_message)
        try:
            num1, operation, num2 = message.split(' ')
        except:
            await print_async('Wrong Format')
            return

        await view.logger.info_async(f'User is requesting `{operation}` operation with numbers: {num1} and {num2}')
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
