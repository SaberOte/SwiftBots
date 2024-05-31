import asyncio
from collections.abc import AsyncGenerator

import pytest

from swiftbots import SwiftBots
from swiftbots.abstract_classes import AbstractMessengerView
from swiftbots.admin_utils import shutdown_app
from swiftbots.all_types import ChatContext, ChatPreContext, IContext
from swiftbots.controllers import Controller
from swiftbots.views import ChatView

global_dict = {}


class MyMessengerView(AbstractMessengerView, ChatView):

    async def _get_updates_async(self) -> AsyncGenerator[dict, None]:
        while True:
            yield {'message': 'TEST command message from', 'sender': 'some sender'}

    async def _deconstruct_message_async(self, update: dict) -> IContext | None:
        return ChatPreContext(message=update['message'], sender=update['sender'])

    async def send_async(self, message, user, data=None):
        await asyncio.sleep(0)
        global global_dict
        global_dict['answer'] = message
        global_dict['user'] = user
        shutdown_app()


class MyController(Controller):

    async def some_command(self, view: ChatView, context: ChatContext):
        mes: str = context.arguments
        await view.send_async(mes + ' command handler', context.sender)

    cmds = {
        'test commAnd': some_command
    }


class TestMessengerView:

    @pytest.mark.timeout(3)
    def test_default_handler(self):
        app = SwiftBots()

        app.add_bot(MyMessengerView, [MyController])

        app.run()

        global global_dict
        assert global_dict['answer'] == 'message from command handler'
        assert global_dict['user'] == 'some sender'
