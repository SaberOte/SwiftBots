import asyncio

from examples.services.calculator_service import CalculatorService, get_calculator_service
from swiftbots import SwiftBots, TelegramBot, depends
from swiftbots.all_types import ILogger


def input_async(*args, **kwargs):
    return asyncio.to_thread(input, *args, **kwargs)


def print_async(*args, **kwargs):
    return asyncio.to_thread(print, *args, **kwargs)


calc_bot = TelegramBot()


@calc_bot.message_handler(commands=['add', '+'])
async def add(message: str, logger: ILogger, chat: calc_bot.Chat,
              calculator: CalculatorService = depends(get_calculator_service)):
    await logger.debug_async(f'User is requesting ADD operation: {message}')
    num1, num2 = message.split(' ')
    result = calculator.add(int(num1), int(num2))
    await chat.reply_async(str(result))


@calc_bot.message_handler(commands=['sub', '-'])
async def subtract(message: str, logger: ILogger, chat: calc_bot.Chat,
                   calculator: CalculatorService = depends(get_calculator_service)):
    await logger.debug_async(f'User is requesting SUBTRACT operation: {message}')
    num1, num2 = message.split(' ')
    result = calculator.sub(int(num1), int(num2))
    await chat.reply_async(str(result))


@calc_bot.default_handler()
async def default_handler(message: str, logger: ILogger, chat: calc_bot.Chat):
    await logger.debug_async(f'User is requesting default handler: {message}')
    await chat.reply_async(f'[default handler] Unknown command: {message}')


app = SwiftBots()

app.add_bots([calc_bot])

app.run()
