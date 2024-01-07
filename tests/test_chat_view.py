import asyncio

from swiftbots.controllers import Controller
from swiftbots.views import ChatView
from swiftbots import initialize_app
from swiftbots.admin_utils import shutdown_app


global_message = ''
global_user = ''


class MyChatView1(ChatView):

    async def listen_async(self):
        while True:
            await asyncio.sleep(0)
            test_value = 'message from'
            yield self.PreContext(test_value, 'some sender')

    async def send_async(self, message, user, data=None):
        await asyncio.sleep(0)
        global global_message, global_user
        global_message = message
        global_user = user
        shutdown_app()


class MyChatView2(ChatView):

    async def listen_async(self):
        while True:
            await asyncio.sleep(0)
            test_value = 'TEST command message from'
            yield self.PreContext(test_value, 'some sender')

    async def send_async(self, message, user, data=None):
        await asyncio.sleep(0)
        global global_message, global_user
        global_message = message
        global_user = user
        shutdown_app()


class MyController(Controller):

    async def default(self, view: ChatView, context: ChatView.Context):
        mes: str = context.raw_message
        await view.send_async(mes + ' default handler', context.sender)

    async def some_command(self, view: ChatView, context: ChatView.Context):
        mes: str = context.arguments
        await view.send_async(mes + ' command handler', context.sender)

    cmds = {
        'test commAnd': some_command,
        'not the same command': print
    }


class TestBasicView:

    def test_default_handler(self):
        app = initialize_app()

        app.add_bot(MyChatView1, [MyController])

        app.run()

        global global_message, global_user
        assert global_message == 'message from default handler'
        assert global_user == 'some sender'

    def test_command(self):
        app = initialize_app()

        app.add_bot(MyChatView2, [MyController])

        app.run()

        global global_message, global_user
        assert global_message == 'message from command handler'
