"""The simplest demonstration how controller may work
with commands and a chat view"""

from swiftbots.types import IChatView
from swiftbots.controllers import Controller


class Notes(Controller):

    async def create(self, view: IChatView, context: IChatView.Context):
        pass

    async def read(self, view: IChatView, context: IChatView.Context):
        pass

    async def update(self, view: IChatView, context: IChatView.Context):
        pass

    async def delete(self, view: IChatView, context: IChatView.Context):
        pass

    async def list_notes(self, view: IChatView, context: IChatView.Context):
        pass

    cmds = {
        '+node': create,
        'note': read,
        '++note': update,
        '-note': delete,
        'notes': list_notes,
    }
