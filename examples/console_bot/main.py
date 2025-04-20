from swiftbots import SwiftBots, Bot


app = SwiftBots()

bot = Bot()


@bot.listener()
async def listen():
    while True:
        message = input('-> ')
        yield {
            'message': message
        }


@bot.handler()
async def handle(message: str):
    print(f'Received message: {message}')


app.add_bots([
    bot
])

app.run()
