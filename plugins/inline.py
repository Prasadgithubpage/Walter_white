import logging
from pyrogram import Client, emoji, filters
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from database.ia_filterdb import get_search_results
from utils import get_size
from info import CACHE_TIME, AUTH_USERS, AUTH_CHANNEL, CUSTOM_FILE_CAPTION

logger = logging.getLogger(__name__)
 # Set an appropriate cache time value in seconds
cache_time = 0 if AUTH_USERS or AUTH_CHANNEL else CACHE_TIME

# Function to check if the user is allowed to use the bot
async def allowed_user(query):
    if AUTH_USERS:
        if query.from_user and query.from_user.id in AUTH_USERS:
            return True
        else:
            return False
    return True

# Function to handle sending files
async def send_file(bot, query, files):
    results = []
    for file in files:
        title = file.file_name
        size = get_size(file.file_size)
        f_caption = file.caption if file.caption else title
        if CUSTOM_FILE_CAPTION:
            try:
                f_caption = CUSTOM_FILE_CAPTION.format(file_name=title, file_size=size, file_caption=f_caption)
            except Exception as e:
                logger.exception(e)
        results.append(
            InlineQueryResultCachedDocument(
                title=title,
                document_file_id=file.file_id,
                caption=f_caption,
                description=f'Size: {size}\nType: {file.file_type}'
            )
        )
    switch_pm_text = f"{emoji.FILE_FOLDER} Results - {len(files)}"
    if query.query:
        switch_pm_text += f" for {query.query}"
    try:
        await query.answer(
            results=results,
            is_personal=True,
            cache_time=cache_time,
            switch_pm_text=switch_pm_text,
            switch_pm_parameter="start"
        )
    except Exception as e:
        logging.exception(str(e))

@Client.on_inline_query()
async def answer(bot, query):
    """Show search results for given inline query"""
    if not await allowed_user(query):
        await query.answer(
            results=[],
            cache_time=0,
            switch_pm_text='You are not authorized to use this bot',
            switch_pm_parameter="start"
        )
        return

    if AUTH_CHANNEL and not await is_subscribed(bot, query):
        await query.answer(
            results=[],
            cache_time=0,
            switch_pm_text='You have to subscribe to use the bot',
            switch_pm_parameter="subscribe"
        )
        return

    results = []
    if '|' in query.query:
        string, file_type = query.query.split('|', maxsplit=1)
        string = string.strip()
        file_type = file_type.strip().lower()
    else:
        string = query.query.strip()
        file_type = None

    offset = int(query.offset or 0)
    files, next_offset, total = await get_search_results(string, file_type=file_type, max_results=10, offset=offset)
    await send_file(bot, query, files)

@Client.on_message(filters.command("search"))
async def search_direct(bot, message):
    query = message.text.split(maxsplit=1)[1]

    logger.info(f"Direct mode search query: {query}")  # Add this line for logging

    files, _, _ = await get_search_results(query, max_results=10)

    if files:
        results = []
        for file in files:
            result = InlineQueryResultCachedDocument(
                title=file.file_name,
                document_file_id=file.file_id,
                caption=file.caption or file.file_name,
                description=f"Size: {get_size(file.file_size)}\nType: {file.file_type}"
            )
            results.append(result)

        try:
            await bot.send_inline_query_result(
                chat_id=message.chat.id,
                query_id=message.message_id,
                results=results
            )
        except Exception as e:
            logger.error(f"Error sending inline query results: {e}")
            await message.reply_text("An error occurred while sending the search results.")
    else:
        await message.reply_text("No matching files found.")
