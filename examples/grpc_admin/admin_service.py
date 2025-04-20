import grpc

import bots_admin_pb2_grpc
from bots_admin_pb2 import StatusReply, BotNameRequest


endpoints = {
    'weather_bot': 'localhost:50051',
    'grpc_server_bot': 'localhost:50051',
}


async def ping_bot(name: str) -> str:
    try:
        async with grpc.aio.insecure_channel(endpoints[name]) as channel:
            stub = bots_admin_pb2_grpc.BotsAdminStub(channel)
            response: StatusReply = await stub.Ping(BotNameRequest(name=name))
        return response.status
    except grpc.aio.AioRpcError:
        return 'no respond'


async def stop_bot(name: str) -> str:
    try:
        async with grpc.aio.insecure_channel(endpoints[name]) as channel:
            stub = bots_admin_pb2_grpc.BotsAdminStub(channel)
            response: StatusReply = await stub.Stop(BotNameRequest(name=name))
        return response.status
    except grpc.aio.AioRpcError:
        return 'no respond'


async def start_bot(name: str) -> str:
    try:
        async with grpc.aio.insecure_channel(endpoints[name]) as channel:
            stub = bots_admin_pb2_grpc.BotsAdminStub(channel)
            response: StatusReply = await stub.Start(BotNameRequest(name=name))
        return response.status
    except grpc.aio.AioRpcError:
        return 'no respond'
