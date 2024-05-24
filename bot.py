import logging
import logging.config
from pyrogram import Client, __version__, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from pyrogram.raw.all import layer
from database.ia_filterdb import Media
from database.users_chats_db import db
from info import SESSION, API_ID, API_HASH, BOT_TOKEN, LOG_STR
from utils import temp
from typing import Union, Optional, AsyncGenerator
from pyrogram import types
from aiohttp import web
from plugins import web_server

PORT = "8080"

# Get logging configurations
logging.config.fileConfig('logging.conf')
logging.getLogger().setLevel(logging.INFO)
logging.getLogger("pyrogram").setLevel(logging.ERROR)
logging.getLogger("imdbpy").setLevel(logging.ERROR)

class Bot(Client):
    def __init__(self):
        super().__init__(
            name=SESSION,
            api_id=API_ID,
            api_hash=API_HASH,
            bot_token=BOT_TOKEN,
            workers=50,
            plugins={"root": "plugins"},
            sleep_threshold=5,
        )
        self.files = []  # To store the list of files

    async def start(self):
        b_users, b_chats = await db.get_banned()
        temp.BANNED_USERS = b_users
        temp.BANNED_CHATS = b_chats
        await super().start()
        await Media.ensure_indexes()
        me = await self.get_me()
        temp.ME = me.id
        temp.U_NAME = me.username
        temp.B_NAME = me.first_name
        self.username = '@' + me.username
        app = web.AppRunner(await self.create_web_server())
        await app.setup()
        bind_address = "0.0.0.0"
        await web.TCPSite(app, bind_address, PORT).start()
        logging.info(f"{me.first_name} with for Pyrogram v{__version__} (Layer {layer}) started on {me.username}.")
        logging.info(LOG_STR)

    async def stop(self, *args):
        await super().stop()
        logging.info("Bot stopped. Bye.")

    async def iter_messages(
        self,
        chat_id: Union[int, str],
        limit: int,
        offset: int = 0,
    ) -> Optional[AsyncGenerator["types.Message", None]]:
        current = offset
        while True:
            new_diff = min(200, limit - current)
            if new_diff <= 0:
                return
            messages = await self.get_messages(chat_id, list(range(current, current+new_diff+1)))
            for message in messages:
                yield message
                current += 1

    async def search_files(self, query: str) -> list:
        # Perform MongoDB search for matching files
        # Replace the below line with actual MongoDB search logic
        files = await Media.search_files(query)
        self.files = files
        return files[:10]

    async def get_file_by_index(self, index: int) -> str:
        # Dummy function to retrieve a file by its index
        if 0 <= index < len(self.files):
            return self.files[index]
        return "File not found"

    async def handle_search(self, request):
        params = await request.json()
        query = params.get('query', '')
        files = await self.search_files(query)
        return web.json_response({"files": files})

    async def handle_get_file(self, request):
        params = await request.json()
        index = int(params.get('index', -1))
        file = await self.get_file_by_index(index)
        return web.json_response({"file": file})

    async def create_web_server(self):
        app = web.Application()
        app.router.add_post('/search_files', self.handle_search)
        app.router.add_post('/get_file', self.handle_get_file)
        return app

    async def on_message(self, message: types.Message):
        query = message.text
        if query:
            files = await self.search_files(query)
            if files:
                keyboard = InlineKeyboardMarkup(
                    [[InlineKeyboardButton(f"{i+1}. {file}", callback_data=f"file_{i}")] for i, file in enumerate(files)]
                )
                await message.reply_text("Top 10 matching results:", reply_markup=keyboard)
            else:
                await message.reply_text("No matching files found.")

app = Bot()
app.run()
