import asyncio

import pytest

from swiftbots import initialize_app
from swiftbots.admin_utils import shutdown_app
from swiftbots.controllers import Controller
from swiftbots.views import BasicView

global_var = 0


class MyBasicView(BasicView):

    async def listen_async(self):
        while True:
            await asyncio.sleep(0)
            test_value = 69
            yield self.PreContext(test_value)

    async def change_var_async(self, value):
        await asyncio.sleep(0)
        global global_var
        global_var = value
        shutdown_app()


class MyController(Controller):

    async def default(self, view: MyBasicView, context: MyBasicView.Context):
        mes: int = context.raw_message
        await view.change_var_async(mes + 2)


class TestBasicView:

    @pytest.mark.timeout(3)
    def test_default_handler(self):
        app = initialize_app()

        app.add_bot(MyBasicView, [MyController])

        app.run()
        assert False
        global global_var
        assert global_var == 71
