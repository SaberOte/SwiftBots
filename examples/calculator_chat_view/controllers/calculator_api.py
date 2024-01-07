"""The simplest demonstration how controller may work
with commands and a chat view"""

from swiftbots.controllers import Controller
from swiftbots.all_types import IChatView


class CalculatorApi(Controller):

    async def add(self, view: IChatView, context: IChatView.Context):
        """Add two numbers"""
        message = context.arguments
        await view.logger.info_async(f'User is requesting ADD operation: {message}')
        num1, num2 = message.split(' ')
        result = float(num1) + float(num2)
        await view.reply_async(str(result), context)

    async def subtract(self, view: IChatView, context: IChatView.Context):
        """
        Subtract two numbers.
        Here is usage context as a dict. So it's possible provide any
        additional information to context and use it in controllers.
        """
        message = context['arguments']
        await view.logger.info_async(f'User is requesting SUBTRACT operation: {message}')
        num1, num2 = message.split(' ')
        result = float(num1) - float(num2)
        await view.reply_async(str(result), context)

    cmds = {
        'add': add,
        '+': add,
        'sub': subtract,
        '-': subtract
    }
