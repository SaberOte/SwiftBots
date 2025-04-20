from swiftbots import SwiftBots, ChatBot

from admin_service import ping_bot, stop_bot, start_bot


app = SwiftBots()

bot = ChatBot(name='admin_bot')


@bot.sender()
async def send_async(message, user):
    print(message)


@bot.listener()
async def listen():
    print('Input a command (list, start <bot>, stop <bot>):')
    while True:
        message = input('-> ')
        yield {
            'message': message,
            'sender': 'Admin'
        }


@bot.message_handler(commands=['list'])
async def print_list_endpoint(chat: bot.Chat):
    result = 'List of bots:'
    bot_names = ['weather_bot', 'grpc_server_bot']
    for name in bot_names:
        status = await ping_bot(name)
        result += f'\n{name}: {status}'
    await chat.reply_async(result)


@bot.message_handler(commands=['stop'])
async def stop_bot_endpoint(chat: bot.Chat, arguments: str):
    status = await stop_bot(arguments.strip())
    await chat.reply_async(status)


@bot.message_handler(commands=['start'])
async def start_bot_endpoint(chat: bot.Chat, arguments: str):
    status = await start_bot(arguments.strip())
    await chat.reply_async(status)


app.add_bots([
    bot
])

app.run()
