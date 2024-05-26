import os
import logging
import random
import asyncio
from Script import script
from pyrogram import Client, filters, enums
from pyrogram.errors import ChatAdminRequired, FloodWait
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from database.ia_filterdb import Media, get_file_details, unpack_new_file_id
from database.users_chats_db import db
from info import CHANNELS, ADMINS, AUTH_CHANNEL, LOG_CHANNEL, PICS, BATCH_FILE_CAPTION, CUSTOM_FILE_CAPTION, PROTECT_CONTENT
from utils import get_settings, get_size, is_subscribed, save_group_settings, temp
from database.connections_mdb import active_connection
import re
import json
import base64
logger = logging.getLogger(__name__)

BATCH_FILES = {}

@Client.on_message(filters.command("start") & filters.incoming)
async def start(client, message):
    if message.chat.type in [enums.ChatType.GROUP, enums.ChatType.SUPERGROUP]:
        await message.reply(script.START_TXT.format(message.from_user.mention if message.from_user else message.chat.title, temp.U_NAME, temp.B_NAME))
        await asyncio.sleep(2) # 😢 https://github.com/EvamariaTG/EvaMaria/blob/master/plugins/p_ttishow.py#L17 😬 wait a bit, before checking.
        if not await db.get_chat(message.chat.id):
            total = await client.get_chat_members_count(message.chat.id)
            await client.send_message(LOG_CHANNEL, script.LOG_TEXT_G.format(message.chat.title, message.chat.id, total, "Unknown"))
            await db.add_chat(message.chat.id, message.chat.title)
        return

    welcome_message = """
Welcome to buym gallery book downloader bot. This bot will give you books from our vast collection of books.

HOW TO USE THE BOT:

JUST TYPE THE NAME OF BOOK AND CLICK ON MOST MATCHING RESULT AND YOU ARE READY TO GO
"""

    # URL of the logo
    logo_url = "https://cdn5.cdn-telegram.org/file/Yu-uD4DVEewOEXJP-Kzd9ZZMa9szshTCrWYSZb70CA5uMba7t3nW9BZPuT4sDuZkEWb2cPNzOvczA8XTtDxyyhc0ZUpQeOXM2OCuXCCenIzvbdcIL1fJCOc79ZJ_PIVXPcdyjfK_6QWiqW2eexHSBsr140gzponnHDSYpAKVNGvWvo9dHAtb3tIPWYtR7pZI95cBPA_lJwZiqb9QyEw3V6SPIyyNB2Nilyo7QUsDg8wk7kNhjSy57hkP3vNr_j7jtDxLeYBxnC4dwyDc2yZzMqLOHSw4tZGGy8eHgIYaYaGiUP5OO56i5U4gOc3A9AY3leZAlc3lBKFOFcRnnGN2zA.jpg"

    # Send the logo image with the welcome message as a caption
    await client.send_photo(
        chat_id=message.chat.id,
        photo=logo_url,
        caption=welcome_message
    )
        
    if not await db.is_user_exist(message.from_user.id):
        await db.add_user(message.from_user.id, message.from_user.first_name)
        await client.send_message(LOG_CHANNEL, script.LOG_TEXT_P.format(message.from_user.id, message.from_user.mention))

    if len(message.command) != 2:
        # Removed the additional welcome message here
        return
    
    if AUTH_CHANNEL and not await is_subscribed(client, message):
        try:
            invite_link = await client.create_chat_invite_link(int(AUTH_CHANNEL))
        except ChatAdminRequired:
            logger.error("Make sure I'm present in your channel!!")
            return
        btn = [
            [
                InlineKeyboardButton(
                    "❤Jᴏɪɴ Uᴘᴅᴀᴛᴇs Cʜᴀɴɴᴇʟ🖤", url=invite_link.invite_link
                )
            ]
        ]

        if message.command[1] != "subscribe":
            try:
                kk, file_id = message.command[1].split("_", 1)
                pre = 'checksubp' if kk == 'filep' else 'checksub' 
                btn.append([InlineKeyboardButton(" 🔄 Tʀʏ Aɢᴀɪɴ", callback_data=f"{pre}#{file_id}")])
            except (IndexError, ValueError):
                btn.append([InlineKeyboardButton(" 🔄 Tʀʏ Aɢᴀɪɴ", url=f"https://t.me/{temp.U_NAME}?start={message.command[1]}")])
        await client.send_message(
            chat_id=message.from_user.id,
            text="**🖤Please Join My Updates Channel to use this Bot❤!**",
            reply_markup=InlineKeyboardMarkup(btn),
            parse_mode=enums.ParseMode.MARKDOWN
        )
        return
    if len(message.command) == 2 and message.command[1] in ["subscribe", "error", "okay", "help"]:
        # Removed the additional welcome message here
        return
    data = message.command[1]
    try:
        pre, file_id = data.split('_', 1)
    except:
        file_id = data
        pre = ""
    if data.split("-", 1)[0] == "BATCH":
        sts = await message.reply("Please wait")
        file_id = data.split("-", 1)[1]
        msgs = BATCH_FILES.get(file_id)
        if not msgs:
            file = await client.download_media(file_id)
            try:
                with open(file) as file_data:
                    msgs = json.loads(file_data.read())
                os.remove(file)
            except:
                await sts.edit("FAILED")
                return await client.send_message(LOG_CHANNEL, "UNABLE TO OPEN FILE.")
            BATCH_FILES[file_id] = msgs
    for msg in msgs:
        title = msg.get("title")
        size = get_size(int(msg.get("size", 0)))
        f_caption = msg.get("caption", "")
        media = msg.get("media")  # Get the 'media' key from the dictionary
        if media:
            try:
                await client.send_cached_media(
                    chat_id=message.from_user.id,
                    file_id=media,  # Use the 'media' value if it exists
                    caption=f_caption
                )
            except FloodWait as e:
                await asyncio.sleep(e.value)
                await client.send_cached_media(
                    chat_id=message.from_user.id,
                    file_id=media,  # Use the 'media' value if it exists
                    caption=f_caption
                )
            except Exception as e:
                logger.exception(e)
        else:
            logger.error("Media key is missing from the message dictionary.")
            return
    sts = await message.reply("Please wait")
    file = await get_file_details(file_id)
    if not file:
        return await sts.edit("No such file exist.")
    for f in file:
        title = f.file_name
        size = get_size(f.file_size)
        f_caption = f.caption
        if CUSTOM_FILE_CAPTION:
            try:
                f_caption = CUSTOM_FILE_CAPTION.format(file_name='' if title is None else title, file_size='' if size is None else size, file_caption='' if f_caption is None else f_caption)
            except Exception as e:
                logger.exception(e)
                f_caption = f_caption
        if f_caption is None:
            f_caption = f"{title}"
        if str(f.file_type) == "Telegram":
            f_d = f.file_id
        else:
            f_d = await unpack_new_file_id(f.file_id)
        try:
            await client.send_cached_media(
                chat_id=message.from_user.id,
                file_id=f_d,
                caption=f_caption,
                protect_content=PROTECT_CONTENT
            )
        except FloodWait as e:
            await asyncio.sleep(e.value)
            await client.send_cached_media(
                chat_id=message.from_user.id,
                file_id=f_d,
                caption=f_caption,
                protect_content=PROTECT_CONTENT
            )
        except Exception as e:
            logger.exception(e)
    await sts.delete()
