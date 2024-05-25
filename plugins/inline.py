import logging
from pyrogram import Client, emoji, filters
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from database.ia_filterdb import get_search_results
from utils import get_size
from info import AUTH_USERS, AUTH_CHANNEL, CUSTOM_FILE_CAPTION

logger = logging.getLogger(__name__)
CACHE_TIME = 300  # Set an appropriate cache time value in seconds
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
    for file in files:
        title = file.file_name
        size = get_size(file.file_size)
        f_caption = file.caption if file.caption else title
        if CUSTOM_FILE_CAPTION:
            try:
                f_caption = CUSTOM_FILE_CAPTION.format(file_name=title, file_size=size, file_caption=f_caption)
            except Exception as e:
                logger.exception(e)

        # Check the file type
        if file.file_type == 'audio':
            try:
                await query.message.reply_audio(
                    audio=file.file_id,
                    caption=f_caption
                )
            except Exception as e:
                logger.error(f"Error sending audio file: {e}")
        else:
            try:
                await query.message.reply_document(
                    document=file.file_id,
                    caption=f_caption
                )
            except Exception as e:
                logger.error(f"Error sending document file: {e}")


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
async def search(bot, message):
    query = message.text.split(maxsplit=1)[1]

    logger.info(f"Search query: {query}")

    files, _, _ = await get_search_results(query, max_results=10)
    if files:
        buttons = [
            [InlineKeyboardButton(file.file_name, callback_data=f"file_{idx}_{query}")]
            for idx, file in enumerate(files)
        ]
        keyboard = InlineKeyboardMarkup(buttons)
        await message.reply_text("Top 10 matching results:", reply_markup=keyboard)
    else:
        await message.reply_text("No matching files found.")

@Client.on_callback_query()
async def callback_handler(bot, query):
    data = query.data
    if data.startswith("file_"):
        try:
            parts = data.split("_")
            file_idx = int(parts[1])
            search_query = parts[2]
            logger.info(f"Callback query search: {search_query}")
            files, _, _ = await get_search_results(search_query, max_results=10)
            logger.info(f"Files retrieved: {files}")
            
            if files and 0 <= file_idx < len(files):
                selected_file = files[file_idx]
                title = selected_file.file_name
                size = get_size(selected_file.file_size)
                f_caption = selected_file.caption if selected_file.caption else title

                if CUSTOM_FILE_CAPTION:
                    try:
                        f_caption = CUSTOM_FILE_CAPTION.format(
                            file_name=title, file_size=size, file_caption=f_caption)
                    except Exception as e:
                        logger.exception(e)

                logger.info(f"Sending file: {selected_file.file_id}")
                if selected_file.file_type == "audio":
                    await query.message.reply_audio(
                        audio=selected_file.file_id,
                        caption=f_caption
                    )
                else:
                    await query.message.reply_document(
                        document=selected_file.file_id,
                        caption=f_caption
                    )
            else:
                await query.answer("No matching files found.", show_alert=True)
        except Exception as e:
            logger.error(f"Error handling callback query: {e}")
            await query.answer("An error occurred while processing your request.", show_alert=True)
