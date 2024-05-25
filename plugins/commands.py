@Client.on_message(filters.command("start") & filters.incoming)
async def start(client, message):
    if message.chat.type in [enums.ChatType.GROUP, enums.ChatType.SUPERGROUP]:
        buttons = [
            [
                InlineKeyboardButton('Walter🎩White', url='https://t.me/mrbhiman44')
            ],
            [
                InlineKeyboardButton('ℹ️ Hᴇʟᴘ', url=f"https://t.me/{temp.U_NAME}?start=help"),
            ]
        ]
        reply_markup = InlineKeyboardMarkup(buttons)
        await message.reply(script.START_TXT.format(message.from_user.mention if message.from_user else message.chat.title, temp.U_NAME, temp.B_NAME), reply_markup=reply_markup)
        await asyncio.sleep(2) # 😢 https://github.com/EvamariaTG/EvaMaria/blob/master/plugins/p_ttishow.py#L17 😬 wait a bit, before checking.
        if not await db.get_chat(message.chat.id):
            total = await client.get_chat_members_count(message.chat.id)
            await client.send_message(LOG_CHANNEL, script.LOG_TEXT_G.format(message.chat.title, message.chat.id, total, "Unknown"))
            await db.add_chat(message.chat.id, message.chat.title)
        return 

    # Check if user is an admin
    if message.chat.type in [enums.ChatType.GROUP, enums.ChatType.SUPERGROUP]:
        user_status = await client.get_chat_member(message.chat.id, message.from_user.id)
        is_admin = user_status.status in [enums.ChatMemberStatus.ADMINISTRATOR, enums.ChatMemberStatus.OWNER]
    else:
        is_admin = False

    # Welcome message for non-admin users
    if not is_admin:
        await message.reply("WELCOME TO BOOK TREASURE BOT. JUST TYPE /SEARCH <BOOK NAME> TO GET STARTED.")
        return

    if not await db.is_user_exist(message.from_user.id):
        await db.add_user(message.from_user.id, message.from_user.first_name)
        await client.send_message(LOG_CHANNEL, script.LOG_TEXT_P.format(message.from_user.id, message.from_user.mention))

    if len(message.command) != 2:
        buttons = [[
            InlineKeyboardButton('➕ Aᴅᴅ Mᴇ Tᴏ Uʀ Gʀᴏᴜᴘs ➕', url=f'http://t.me/{temp.U_NAME}?startgroup=true')
            ],[
            InlineKeyboardButton('🔍 Sᴇᴀʀᴄʜ', switch_inline_query_current_chat=''),
            InlineKeyboardButton('Walter🎩White', url='https://t.me/mrbhiman44')
            ],[
            InlineKeyboardButton('ℹ️ Hᴇʟᴘ', callback_data='help'),
            InlineKeyboardButton('👩‍💻 Rᴇᴘᴏ', url='https://github.com/MRbhiman/Walter_white/tree/Master'),
            InlineKeyboardButton('😊 Aʙᴏᴜᴛ', callback_data='about')
        ]]
        reply_markup = InlineKeyboardMarkup(buttons)
        await message.reply_photo(
            photo=random.choice(PICS),
            caption=script.START_TXT.format(message.from_user.mention, temp.U_NAME, temp.B_NAME),
            reply_markup=reply_markup,
            parse_mode=enums.ParseMode.HTML
        )
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
        buttons = [[
            InlineKeyboardButton('➕ Aᴅᴅ Mᴇ Tᴏ Uʀ Gʀᴏᴜᴘs ➕', url=f'http://t.me/{temp.U_NAME}?startgroup=true')
            ],[
            InlineKeyboardButton('🔍 Sᴇᴀʀᴄʜ', switch_inline_query_current_chat=''),
            InlineKeyboardButton('Walter🎩White', url='https://t.me/mrbhiman44')
            ],[
            InlineKeyboardButton('ℹ️ Hᴇʟᴘ', callback_data='help'),
            InlineKeyboardButton('👩‍💻 Rᴇᴘᴏ', url='https://github.com/MRbhiman/Walter_white/tree/Master'),
            InlineKeyboardButton('😊 Aʙᴏᴜᴛ', callback_data='about')
        ]]
        reply_markup = InlineKeyboardMarkup(buttons)
        await message.reply_photo(
            photo=random.choice(PICS),
            caption=script.START_TXT.format(message.from_user.mention, temp.U_NAME, temp.B_NAME),
            reply_markup=reply_markup,
            parse_mode=enums.ParseMode.HTML
        )
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
            except:
                await sts.edit("FAILED")
                return await client.send_message(LOG_CHANNEL, "UNABLE TO OPEN FILE.")
            os.remove(file)
            BATCH_FILES[file_id] = msgs
        for msg in msgs:
            title = msg.get("title")
            size = get_size(int(msg.get("size", 0)))
            f_caption = msg.get("caption", "")
            if BATCH_FILE_CAPTION:
                try:
                    f_caption = BATCH_FILE_CAPTION.format(file_name='' if title is None else title, file_size='' if size is None else size, file_caption='' if f_caption is None else f_caption)
                except Exception as e:
                    logger.exception(e)
                    f_caption = f_caption
            if f_caption is None:
                f_caption = f"{title}"
            try:
                await client.send_cached_media(
                    chat_id=message.from_user.id,
                    file_id=msg.get("file_id"),
                    caption=f_caption,
                    protect_content=msg.get('protect', False),
                )
            except FloodWait as e:
                await asyncio.sleep(e.x)
                logger.warning(f"Floodwait of {e.x} sec.")
                await client.send_cached_media(
                    chat_id=message.from_user.id,
                    file_id=msg.get("file_id"),
                    caption=f_caption,
                    protect_content=msg.get('protect', False),
                )
            except Exception as e:
                logger.warning(e, exc_info=True)
                continue
            await asyncio.sleep(1)
        await sts.delete()
        return
    elif data.split("-", 1)[0] == "DSTORE":
        sts = await message.reply("Please wait")
        b_string = data.split("-", 1)[1]
        decoded = (base64.urlsafe_b64decode(b_string + "=" * (-len(b_string) % 4))).decode("ascii")
        try:
            f_msg_id, l_msg_id, f_chat_id, protect = decoded.split("_", 3)
        except:
            f_msg_id, l_msg_id, f_chat_id = decoded.split("_", 2)
            protect = "/pbatch" if PROTECT_CONTENT else "batch"
        diff = int(l_msg_id) - int(f_msg_id)
        async for msg in client.iter_messages(int(f_chat_id), int(l_msg_id), int(f_msg_id)):
            if msg.media:
                media = getattr(msg, msg.media.value)
                if BATCH_FILE_CAPTION:
                    try:
                        f_caption = BATCH_FILE_CAPTION.format(file_name='' if media.title is None else media.title, file_size='' if media.size is None else get_size(media.size), file_caption='' if msg.caption is None else msg.caption)
                    except Exception as e:
                        logger.exception(e)
                        f_caption = msg.caption
                else:
                    f_caption = msg.caption
                try:
                    await client.send_cached_media(
                        chat_id=message.from_user.id,
                        file_id=media.file_id,
                        caption=f_caption,
                        protect_content=True if protect == "/pbatch" else False,
                    )
                except FloodWait as e:
                    await asyncio.sleep(e.x)
                    logger.warning(f"Floodwait of {e.x} sec.")
                    await client.send_cached_media(
                        chat_id=message.from_user.id,
                        file_id=media.file_id,
                        caption=f_caption,
                        protect_content=True if protect == "/pbatch" else False,
                    )
                except Exception as e:
                    logger.warning(e, exc_info=True)
                    continue
                await asyncio.sleep(1)
        await sts.delete()
        return
    elif pre.lower() == "filep":
        await show_file(client, message, file_id, True)
    elif pre.lower() == "file":
        await show_file(client, message, file_id)
    elif pre.lower() == "checksubp":
        if await is_subscribed(client, message):
            await show_file(client, message, file_id, True)
        else:
            await message.reply("Please join the channel first.")
    elif pre.lower() == "checksub":
        if await is_subscribed(client, message):
            await show_file(client, message, file_id)
        else:
            await message.reply("Please join the channel first.")
    else:
        await message.reply("Invalid Command!")
