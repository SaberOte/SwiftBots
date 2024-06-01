import asyncio

import pytest

from swiftbots import PeriodTrigger, SwiftBots, task
from swiftbots.admin_utils import shutdown_app
from swiftbots.controllers import Controller
from swiftbots.views import BasicView

global_var = 0


class MyBasicView(BasicView):

    async def listen_async(self):
        await asyncio.sleep(100)

    async def change_var(self, value):
        await asyncio.sleep(0)
        global global_var
        global_var = value
        shutdown_app()


class MyController(Controller):

    @task('my-task', PeriodTrigger(seconds=5), run_at_start=True)
    async def my_task_method(self, view: MyBasicView):
        await view.change_var(5)


class _TestBasicView:

    # @pytest.mark.timeout(3)
    def test_default_handler(self):
        app = SwiftBots()

        app.add_bot(MyBasicView, [MyController])

        app.run()

        global global_var
        assert global_var == 71
