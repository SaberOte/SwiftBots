"""The simplest demonstration how controller may work
with commands and a chat view"""

from swiftbots.types import IChatView
from swiftbots.controllers import Controller


class Notes(Controller):

    async def add(self, view: IChatView, context: IChatView.Context):
        pass

    async def remove(self, view: IChatView, context: IChatView.Context):
        pass

    async def list_notes(self, view: IChatView, context: IChatView.Context):
        pass

    async def update_note(self, view: IChatView, context: IChatView.Context):
        pass

    cmds = {
        '+node': add,
        '-note': remove,
        'notes': list_notes,
        '++note': update_note
    }
