import asyncio

import pytest

from swiftbots import PeriodTrigger, SwiftBots, task
from swiftbots.admin_utils import shutdown_app
from swiftbots.controllers import Controller
from swiftbots.views import StubView

global_var = 0


class MyBasicView(StubView):

    async def change_var(self, value):
        await asyncio.sleep(0)
        global global_var
        global_var = value
        shutdown_app()


class MyController(Controller):
    async def default(self):
        ...


@task(PeriodTrigger(seconds=5), run_at_start=False, name='my-task')
async def my_task_method(view: MyBasicView):
    await view.change_var(5)


class TestBotTasks:

    @pytest.mark.timeout(5)
    def test_default_handler(self):
        app = SwiftBots()

        app.add_bot(MyBasicView, [MyController], tasks=[my_task_method])

        app.run()

        global global_var
        assert global_var == 5
