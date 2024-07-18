import os

from examples.services.calculator_service import CalculatorService, get_calculator_service
from swiftbots import SwiftBots, VkontakteBot, depends
from swiftbots.all_types import ILogger

token = os.environ.get('TOKEN')
group_id = os.environ.get('GROUP_ID')
assert token, 'Missing environment variable "TOKEN"'
assert group_id, 'Missing environment variable "GROUP_ID"'
admin = os.environ.get('ADMIN')

calc_bot = VkontakteBot(token, group_id, admin, name='My Vk Bot')


@calc_bot.message_handler(commands=['sub', '-'])
async def subtract(message: str, logger: ILogger, chat: calc_bot.Chat,
                   calculator: CalculatorService = depends(get_calculator_service)):
    await logger.debug_async(f'User is requesting SUBTRACT operation: {message}')
    num1, num2 = message.split(' ')
    result = calculator.sub(int(num1), int(num2))
    await chat.reply_async(str(result))


@calc_bot.message_handler(commands=['add', '+'])
async def add(message: str, logger: ILogger, chat: calc_bot.Chat,
              calculator: CalculatorService = depends(get_calculator_service)):
    await logger.debug_async(f'User is requesting ADD operation: {message}')
    num1, num2 = message.split(' ')
    result = calculator.add(int(num1), int(num2))
    await chat.reply_async(str(result))


@calc_bot.default_handler()
async def default_handler(message: str, logger: ILogger, chat: calc_bot.Chat):
    await logger.debug_async(f'User is requesting default handler: {message}')
    await chat.reply_async(f'[default handler] Unknown command: {message}')


app = SwiftBots()

app.add_bots([calc_bot])

app.run()
