import asyncio

import pytest

from swiftbots import SwiftBots
from swiftbots.admin_utils import shutdown_app
from swiftbots.all_types import BasicContext, BasicPreContext
from swiftbots.controllers import Controller
from swiftbots.views import BasicView

global_var = 0


class MyBasicView(BasicView):

    async def listen_async(self):
        while True:
            await asyncio.sleep(0)
            test_value = 69
            yield BasicPreContext(test_value)

    async def change_var_async(self, value):
        await asyncio.sleep(0)
        global global_var
        global_var = value
        shutdown_app()


class MyController(Controller):

    async def default(self, view: MyBasicView, context: BasicContext):
        mes: int = context['raw_message']
        await view.change_var_async(mes + 2)


class TestBasicView:

    @pytest.mark.timeout(3)
    def test_default_handler(self):
        app = SwiftBots()

        app.add_bot(MyBasicView, [MyController])

        app.run()

        global global_var
        assert global_var == 71
