"""
The demonstration how to use sqlalchemy ORM.
Tutorial: https://docs.sqlalchemy.org/en/20/orm/extensions/asyncio.html#synopsis-orm
"""

import re

from datetime import datetime as dt

from sqlalchemy import select
from swiftbots.types import IChatView
from swiftbots.controllers import Controller

from examples.notes_in_database.models.notes import Note


class Notes(Controller):

    compiled_note_pattern = re.compile(rf'^(\S+)\s+(\S+.*)$', re.IGNORECASE | re.DOTALL)

    async def create(self, view: IChatView, context: IChatView.Context):
        message = context.arguments

        match = self.compiled_note_pattern.match(message)

        if not match:
            await view.reply_async("There are no name or text of new note. "
                                   "Use the command like '+note note_name text_of_note'", context)
            return

        name = match.group(1)
        text = match.group(2)

        async with self.async_db_session_maker() as session:
            note = await session.scalar(select(Note)
                                        .where(Note.name == name))

            # Note already exists
            if note is not None:
                await view.reply_async(f"Note '{name}' already exists. And it's overwritten. "
                                       f"Its previous text is:\n{note.text}", context)
                note.text = text
                note.modified = dt.utcnow()

            # Note doesn't exist
            else:
                session.add(Note(name=name, text=text))

            await session.commit()
            await view.reply_async("Notes updated", context)

    async def read(self, view: IChatView, context: IChatView.Context):
        name = context.arguments
        if not name:
            await view.reply_async("No note name given", context)

        async with self.async_db_session_maker() as session:
            note = await session.scalar(select(Note)
                                        .where(Note.name == name))

            if note is None:
                await view.reply_async("There's no note with such name", context)
                return
            await view.reply_async(note.text, context)

    async def update(self, view: IChatView, context: IChatView.Context):
        message = context.arguments

        match = self.compiled_note_pattern.match(message)

        if not match:
            await view.reply_async("There are no name or text of new note. "
                                   "Use the command like '++note note_name text_to_add'", context)
            return

        name = match.group(1)
        text = match.group(2)

        async with self.async_db_session_maker() as session:
            note = await session.scalar(select(Note)
                                        .where(Note.name == name))

            # Note doesn't exist
            if note is None:
                await view.reply_async("There's no such note", context)
                return

            # Note exists
            note.text += '\n' + text
            note.modified = dt.utcnow()
            await session.commit()
            await view.reply_async("Notes updated", context)

    async def delete(self, view: IChatView, context: IChatView.Context):
        name = context.arguments

        async with self.async_db_session_maker() as session:
            note = await session.scalar(select(Note)
                                        .where(Note.name == name))

            # Note doesn't exist
            if note is None:
                await view.reply_async("There's no such note", context)
                return

            # Note exists
            await session.delete(note)
            await session.commit()
            await view.reply_async("Notes updated", context)

    async def list_notes(self, view: IChatView, context: IChatView.Context):
        async with self.async_db_session_maker() as session:
            notes = (await session.scalars(select(Note.name)
                                           .order_by(Note.modified))).all()

            if len(notes) == 0:
                await view.reply_async("No notes", context)
            else:
                msg = '\n'.join(notes)
                await view.reply_async(msg, context)

    cmds = {
        '+note': create,
        'note': read,
        '++note': update,
        '-note': delete,
        'notes': list_notes,
    }
