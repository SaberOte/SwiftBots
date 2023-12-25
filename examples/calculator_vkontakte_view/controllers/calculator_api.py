"""The simplest demonstration how controller may work
with commands and a vkontakte view"""

from swiftbots.types import IVkontakteView
from swiftbots.controllers import Controller
from swiftbots.admin_utils import admin_only_async


class CalculatorApi(Controller):

    async def add(self, view: IVkontakteView, context: IVkontakteView.Context):
        """Add two numbers"""
        message = context.arguments
        self.info(f'User is requesting ADD operation: {message}')
        num1, num2 = message.split(' ')
        result = float(num1) + float(num2)
        await view.send_async(str(result), context)

    @admin_only_async
    async def subtract(self, view: IVkontakteView, context: IVkontakteView.Context):
        """
        Subtract two numbers.
        Here is usage context as a dict. So it's possible provide any
        additional information to context and use it in controllers.
        """
        message = context['arguments']
        self.info(f'User is requesting SUBTRACT operation: {message}')
        num1, num2 = message.split(' ')
        result = float(num1) - float(num2)
        await view.send_async(str(result), context)

    cmds = {
        'add': add,
        '+': add,
        'sub': subtract,
        '-': subtract
    }
