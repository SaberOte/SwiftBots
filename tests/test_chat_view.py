import asyncio

import pytest

from swiftbots import ChatBot, SwiftBots
from swiftbots.admin_utils import shutdown_app

global_dict = {}


bot = ChatBot()


@bot.message_handler(commands=['command 1'])
async def command_handler_1(message: str, chat: bot.Chat):
    await chat.reply_async(message + ' from command handler 1')


@bot.message_handler(commands=['command 2'])
async def never_should_be_called():
    raise Exception()


@bot.default_handler()
async def default_handler(message: str, chat: bot.Chat):
    await chat.reply_async(message + ' from default handler')


@bot.sender()
async def send_async(message, user):
    await asyncio.sleep(0)
    print(f'Message: {message} sent to {user}')
    global global_dict
    global_dict['answer1'] = message
    global_dict['user1'] = user
    shutdown_app()


class TestChatBot:

    @pytest.mark.timeout(3)
    def test_message_handler(self):
        app = SwiftBots()

        @bot.listener()
        async def listen_async():
            while True:
                await asyncio.sleep(0)
                test_value = 'Command 1  unique message'
                sender = 'Hund'
                yield {
                    "message": test_value,
                    "sender": sender
                }

        app.add_bots([bot])

        app.run()

        global global_dict
        assert global_dict['answer1'] == 'unique message from command handler 1'
        assert global_dict['user1'] == 'Hund'

    @pytest.mark.timeout(3)
    def test_default_handler(self):
        app = SwiftBots()

        @bot.listener()
        async def listen_async():
            while True:
                await asyncio.sleep(0)
                test_value = 'Unknown command'
                sender = 'Pferd'
                yield {
                    "message": test_value,
                    "sender": sender
                }

        app.add_bots([bot])

        app.run()

        global global_dict
        assert global_dict['answer1'] == 'Unknown command from default handler'
        assert global_dict['user1'] == 'Pferd'
