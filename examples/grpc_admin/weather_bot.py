import asyncio

import grpc
from swiftbots import SwiftBots, Bot, StubBot
from swiftbots.admin_utils import get_bot_names_async, shutdown_bot_async, start_bot_async
from swiftbots.all_types import StartBotException


import bots_admin_pb2_grpc
from bots_admin_pb2 import StatusReply, BotNameRequest


def input_async(*args, **kwargs):
    return asyncio.to_thread(input, *args, **kwargs)


db = {
    'Beijing': '+18°C, wind 8 km/h, humidity 50%',
    'Lisbon': '+14°C, wind 16 km/h, humidity 66%',
    'Montevideo': '+16°C, wind 13 km/h, humidity 69%'
}

app = SwiftBots()

weather_bot = Bot(name='weather_bot')


@weather_bot.listener()
async def listen():
    print('Input a city to get weather (only Beijing, Lisbon, Montevideo):')
    while True:
        city = await input_async('-> ')
        yield {
            'city': city
        }


@weather_bot.handler()
async def handle(city: str):
    city = city.capitalize()
    report = db.get(city)
    if report:
        print(f'Weather report for {city}: {report}')
    else:
        print(f'No weather report for {city} (only Beijing, Lisbon, Montevideo)')


# Api for handling requests from admin bot
grpc_server_bot = StubBot(name='grpc_server_bot')

class BotsAdminServices(bots_admin_pb2_grpc.BotsAdminServicer):
    async def Ping(self, request: BotNameRequest, context) -> StatusReply:
        existing_bots, running_bots, _ = await get_bot_names_async()
        if not request.name in existing_bots:
            return StatusReply(status='unknown')
        if request.name in running_bots:
            return StatusReply(status='active')
        return StatusReply(status='inactive')

    async def Stop(self, request: BotNameRequest, context) -> StatusReply:
        is_stopped = await shutdown_bot_async(request.name)
        return StatusReply(status='stopped' if is_stopped else 'failed to stop')

    async def Start(self, request: BotNameRequest, context) -> StatusReply:
        status = await start_bot_async(request.name)
        if status == 1:
            result = 'already running'
        elif status == 2:
            result = 'unknown bot'
        else:
            result = 'unknown status'
        return StatusReply(status=result)


@grpc_server_bot.listener()
async def listen():
    server = grpc.aio.server()
    bots_admin_pb2_grpc.add_BotsAdminServicer_to_server(BotsAdminServices(), server)
    listen_addr = '[::]:50051'
    server.add_insecure_port(listen_addr)
    grpc_server_bot.logger.info(f'Starting server on {listen_addr}')
    await server.start()
    await server.wait_for_termination()
    yield {}


app.add_bots([
    weather_bot,
    grpc_server_bot
])

app.run()
