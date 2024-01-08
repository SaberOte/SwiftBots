import asyncio

import pytest

from swiftbots import initialize_app
from swiftbots.admin_utils import shutdown_app
from swiftbots.all_types import ChatContext, ChatPreContext
from swiftbots.controllers import Controller
from swiftbots.views import ChatView

global_dict = {}


class MyChatView1(ChatView):

    async def listen_async(self):
        while True:
            await asyncio.sleep(0)
            test_value = 'message from'
            yield ChatPreContext(test_value, 'some sender')

    async def send_async(self, message, user, data=None):
        await asyncio.sleep(0)
        global global_dict
        global_dict['answer1'] = message
        global_dict['user1'] = user
        shutdown_app()


class MyChatView2(ChatView):

    async def listen_async(self):
        while True:
            await asyncio.sleep(0)
            test_value = 'TEST command message from'
            yield ChatPreContext(test_value, 'some sender')

    async def send_async(self, message, user, data=None):
        await asyncio.sleep(0)
        global global_dict
        global_dict['answer2'] = message
        global_dict['user2'] = user
        shutdown_app()


class MyController(Controller):

    async def default(self, view: ChatView, context: ChatContext):
        mes: str = context.raw_message
        await view.send_async(mes + ' default handler', context.sender)

    async def some_command(self, view: ChatView, context: ChatContext):
        mes: str = context.arguments
        await view.send_async(mes + ' command handler', context.sender)

    cmds = {
        'test commAnd': some_command,
        'not the same command': print
    }


class TestBasicView:

    @pytest.mark.timeout(3)
    def test_default_handler(self):
        app = initialize_app()

        app.add_bot(MyChatView1, [MyController])

        app.run()

        global global_dict
        assert global_dict['answer1'] == 'message from default handler'
        assert global_dict['user1'] == 'some sender'

    @pytest.mark.timeout(3)
    def test_command(self):
        app = initialize_app()

        app.add_bot(MyChatView2, [MyController])

        app.run()

        global global_dict
        assert global_dict['answer2'] == 'message from command handler'
        assert global_dict['user2'] == 'some sender'
