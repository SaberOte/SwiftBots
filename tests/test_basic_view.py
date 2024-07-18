import asyncio

import pytest

from swiftbots import Bot, SwiftBots
from swiftbots.admin_utils import shutdown_app

global_dict = {}


bot = Bot()


@bot.handler()
async def the_one_handler(value: str):
    await asyncio.sleep(0)
    global global_dict
    global_dict['value'] = value
    shutdown_app()


@bot.listener()
async def listen_async():
    while True:
        await asyncio.sleep(0)
        test_value = 'Some value'
        yield {
            "value": test_value
        }


class TestBasicBot:

    @pytest.mark.timeout(3)
    def test_base_handler(self):
        app = SwiftBots()

        app.add_bots([bot])

        app.run()

        global global_dict
        assert global_dict['value'] == 'Some value'
