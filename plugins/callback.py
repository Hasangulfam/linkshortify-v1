import asyncio
import logging
import os
import re
import sys
from datetime import datetime

from config import Config
from database import update_user_info
from database.users import add_user_forward_channel, get_user, is_user_verified, remove_user_forward_channel
from helpers import Helpers, temp
from pyrogram import Client, filters, enums
from pyrogram.types import (CallbackQuery, InlineKeyboardButton,
                            InlineKeyboardMarkup)
from plugins.commands import forward_channels_handler, watermark_handler
from translation import (
    ABOUT_REPLY_MARKUP, BACK_REPLY_MARKUP, HELP_REPLY_MARKUP)
from utils import get_font_image, get_font_list, get_me_button, is_float, search_file

logger = logging.getLogger(__name__)


@Client.on_callback_query(filters.regex(r"^setgs"))
async def user_setting_cb(c: Client, query: CallbackQuery):
    _, setting, toggle, user_id = query.data.split('#')
    myvalues = {setting: toggle == "True"}
    await update_user_info(user_id, myvalues)
    user = await get_user(user_id)
    buttons = await get_me_button(user)
    reply_markup = InlineKeyboardMarkup(buttons)
    try:
        await query.message.edit_reply_markup(reply_markup)
        setting = (re.sub(r"is|_", " ", setting)).title()
        toggle = "Enabled" if toggle == "True" else "Disabled"
        await query.answer(f"{setting} {toggle} Successfully", show_alert=True)
    except Exception as e:
        logging.error(
            "Errors occurred while updating user information", exc_info=True)


@Client.on_callback_query(filters.regex(r"^add_forward_channel$"))
async def add_forward_channel(client: Client, query: CallbackQuery):
    markup = InlineKeyboardMarkup(
        [[InlineKeyboardButton(
            "Add Channel", callback_data="add_forward_channel")]]
    )
    text = "Forward me a message from the channel you want to add."
    user_id = query.from_user.id
    message: query.message = await query.message.chat.ask(text, timeout=60)

    if not message.forward_from_chat:
        return await message.reply_text(
            "**Forward a message from the channel you want to add**",
            reply_markup=markup
        )

    if message.forward_from_chat.type != enums.ChatType.CHANNEL:
        return await message.reply_text(
            "Forward a message from the channel you want to add",
            reply_markup=markup
        )

    channel_id = message.forward_from_chat.id

    try:
        await client.get_chat_member(channel_id, client.me.id)
    except:
        return await message.reply_text("Add the bot as admin to the channel first", reply_markup=markup)

    try:
        channel = await client.get_chat(channel_id)
        member = await client.get_chat_member(channel_id, client.me.id)

        if member.status != enums.ChatMemberStatus.ADMINISTRATOR:
            return await message.reply_text(
                "Make sure the bot is an admin of the channel",
                reply_markup=markup
            )
        is_user_admin = await client.get_chat_member(channel_id, message.from_user.id)

        if is_user_admin.status not in [
            enums.ChatMemberStatus.ADMINISTRATOR,
            enums.ChatMemberStatus.OWNER,
        ]:
            return await message.reply_text(
                "**😶‍🌫️ You are not an admin of the channel**",
                reply_markup=markup
            )
    except:
        return await message.reply_text(
            "**Channel not found❌️ \n make sure the bot is an admin of the channel**",
            reply_markup=markup
        )

    await add_user_forward_channel(user_id, channel_id)

    markup = InlineKeyboardMarkup(
        [[InlineKeyboardButton(
            "Back", callback_data="view_forward_channels")]]
    )
    await message.reply_text("Channel added", reply_markup=markup)


@Client.on_callback_query(filters.regex(r"^view_forward_channels$"))
async def view_forward_channels(client: Client, query: CallbackQuery):
    await forward_channels_handler(client, query)


@Client.on_callback_query(filters.regex(r"^ask_delete_forward_channel#"))
async def ask_delete_forward_channel(client: Client, query: CallbackQuery):
    _, channel_id = query.data.split('#')
    channel_id = int(channel_id)
    channel = await client.get_chat(channel_id)
    markup = InlineKeyboardMarkup(
        [[InlineKeyboardButton(
            "Delete Channel", callback_data=f"delete_forward_channel#{channel_id}")]]
    )
    await query.message.reply(f"Are you sure you want to delete {channel.title}?", reply_markup=markup)


@Client.on_callback_query(filters.regex(r"^delete_forward_channel#"))
async def delete_forward_channel(client: Client, query: CallbackQuery):
    _, channel_id = query.data.split('#')
    user_id = query.from_user.id
    await remove_user_forward_channel(user_id, int(channel_id))
    await query.message.delete()
    await query.answer("Channel removed", show_alert=True)

    markup = InlineKeyboardMarkup(
        [[InlineKeyboardButton(
            "Back", callback_data="view_forward_channels")]]
    )
    await query.message.reply_text("Channel removed successfully", reply_markup=markup)


@Client.on_callback_query(filters.regex("^watermark_settings$"))
async def watermark_cb_handler(c: Client, m: CallbackQuery):
    await watermark_handler(c, m)


@Client.on_callback_query(filters.regex("^forward_post#"))
async def forward_post_cb_handler(c: Client, m: CallbackQuery):
    _, user_id = m.data.split("#")
    user_id = int(user_id)
    user = await get_user(user_id)
    channels = user["forward_channels"]["channels"]
    if not channels:
        return await m.answer("No channel found", show_alert=True)

    m.message.reply_markup.inline_keyboard.pop() if m.message.reply_markup else None
    if not m.message.reply_markup or not m.message.reply_markup.inline_keyboard:
        m.message.reply_markup = None

    for channel in channels:
        try:
            await m.message.copy(channel, caption=m.message.caption.html, reply_markup=m.message.reply_markup)
        except Exception as e:
            print(e)
    await m.answer("Post forwarded to all channels", show_alert=True)


@Client.on_callback_query(filters.regex("^boolsettings"))
async def boolsettings_settings(c: Client, m: CallbackQuery):
    _, setting, status = m.data.split("#")
    status = status == "True"
    await update_user_info(m.from_user.id, {setting: status})
    staus_text = "Enabled ✅" if status else "Disabled ❌"
    await m.answer(f"{staus_text} Sucessfully", show_alert=True)

    if "watermark" in setting:
        data = "watermark_settings"
    else:
        data = "view_forward_channels"
    button = [[InlineKeyboardButton(
        "Back", callback_data=data)]]
    await m.message.edit("Setting updated ✅", reply_markup=InlineKeyboardMarkup(button))


@Client.on_callback_query(filters.regex("^set_watermark_text$"))
async def set_watermark_text(c: Client, m: CallbackQuery):

    watermark = await m.message.chat.ask(
        "Send me a watermark text, to cancel /cancel", timeout=60
    )
    button = InlineKeyboardButton
    markup = InlineKeyboardMarkup
    await watermark.request.delete()
    await watermark.delete()

    if not watermark.text:
        await m.message.edit(
            "Invalid Text",
            reply_markup=markup(
                [[button("Back", callback_data="watermark_settings")]]),
        )

    elif watermark.text == "/cancel":
        await m.message.edit(
            "Cancelled",
            reply_markup=markup(
                [[button("Back", callback_data="watermark_settings")]]),
        )
    else:
        await m.message.edit(
            "Watermark Set", reply_markup=markup([[button("Back", callback_data="watermark_settings")]])),

        await update_user_info(
            m.from_user.id, {"watermark.watermark_text": watermark.text}
        )
    return


@Client.on_callback_query(filters.regex("^watermark_"))
async def watermark(c: Client, m: CallbackQuery):

    button = InlineKeyboardButton
    markup = InlineKeyboardMarkup
    _, data = m.data.split("_")
    user_config = await get_user(m.from_user.id)
    fonts = [(x, x) for x in await get_font_list()]
    colors_list = [
        "white",
        "black",
        "red",
        "green",
        "blue",
        "yellow",
        "orange",
        "purple",
        "pink",
        "brown",
    ]
    # get emoji with color name
    color_emoji = {
        "white": "⚪",
        "black": "⚫",
        "red": "🔴",
        "green": "🟢",
        "blue": "🔵",
        "yellow": "🟡",
        "orange": "🟠",
        "purple": "🟣",
        "pink": "🟣",
        "brown": "🟤",
    }
    settings_list = {
        "color": [(color, f"{color.capitalize()} {color_emoji[color]}") for color in colors_list],
        "text": [("set_watermark_text", "Set Watermark Text")],
        "position": [
            ("top-left", "↖️"),
            ("top-center", "⬆️"),
            ("top-right", "↗️"),
            ("center-left", "⬅️"),
            ("center-center", "🔳"),
            ("center-right", "➡️"),
            ("bottom-left", "↙️"),
            ("bottom-center", "⬇️"),
            ("bottom-right", "↘️"),
        ],
        "size": [(i, i) for i in range(5, 101, 5)],
        "font": fonts,
        "opacity": [(i, i) for i in [round(x * 0.1, 1) for x in range(1, 11)]],
    }

    # Create a list to hold the buttons
    buttons = []

    # Create a list to hold the buttons in a row
    row_buttons = []
    settings = settings_list.get(data)
    # Loop through the settings list
    for setting, text in settings:
        # Create a button for each setting
        button_text = text

        data_type = "int" if str(setting).isdigit() else "float" if is_float(
            setting) else "list" if "-" in setting else "str"

        if setting == "set_watermark_text":
            button_data = setting
        elif data == "font":
            button_data = f"font#{setting}"
        else:
            button_data = f"boolwatermark#{data}#{setting}#{data_type}"

        # Add the button to the row
        row_buttons.append(button(button_text, callback_data=button_data))

        # If the row has three buttons, add it to the list of buttons

        if (
            data == "position"
            and len(row_buttons) == 3
            or data != "position"
            and len(row_buttons) == 2
        ):
            buttons.append(row_buttons)
            row_buttons = []
    # If the last row doesn't have three buttons, add empty buttons to fill the row
    if len(row_buttons) > 0:
        buttons.append(row_buttons)

    # Add the status button to the list of buttons
    buttons.extend(
        (
            [button("Back", callback_data="watermark_settings")],
        )
    )

    # Create the reply markup
    reply_markup = markup(buttons)

    data_value = user_config["watermark"].get(f"watermark_{data}")

    if type(data_value) == list:
        data_value = ", ".join(data_value)

    # Edit the message
    await m.message.edit(f"Watermark {data.title()} Settings\nCurrent Value: {data_value}", reply_markup=reply_markup)


@Client.on_callback_query(filters.regex("^boolwatermark#"))
async def boolwatermark(c: Client, m: CallbackQuery):
    button = InlineKeyboardButton
    markup = InlineKeyboardMarkup
    _, data, value, data_type = m.data.split("#")
    if data_type == "int":
        value = int(value)
    elif data_type == "float":
        value = float(value)
    elif data_type == "list":
        value = value.split("-")

    await update_user_info(m.from_user.id, {f"watermark.watermark_{data}": value})

    if type(value) == list:
        value = ", ".join(value)

    await m.message.edit(f"Watermark {data.title()} Settings\nCurrent Value: {value}", reply_markup=markup([[button("Back", callback_data="watermark_settings")]]))


@Client.on_callback_query(filters.regex("^font#"))
async def font(c: Client, m: CallbackQuery):
    try:
        sts = await m.message.reply("Loading Font...", quote=True)
        _, font = m.data.split("#")
        button = InlineKeyboardButton
        markup = InlineKeyboardMarkup
        font_file = await search_file(Config.FONT_DIR, f"{font}")

        if not font_file:
            await m.message.edit("Invalid Font")
            return

        font_image = await get_font_image(font, font)

        reply_markup = markup(
            [
                [
                    button("Set Font", callback_data=f"set_font#{font}"),
                    button("Back", callback_data="watermark_settings")
                ]
            ])
        await m.message.reply_photo(font_image, caption=f"Font: {font}", reply_markup=reply_markup)
        os.remove(font_image)
        await sts.delete()
    except Exception as e:
        print(e)


@Client.on_callback_query(filters.regex("^set_font#"))
async def set_font(c: Client, m: CallbackQuery):
    _, font = m.data.split("#")
    button = InlineKeyboardButton
    markup = InlineKeyboardMarkup
    user = await get_user(m.from_user.id)
    if not user:
        await m.answer("User not found!")
        return
    await update_user_info(m.from_user.id, {"watermark.watermark_font": font})
    await m.message.edit(f"Font Set: {font}", reply_markup=markup([[button("Back", callback_data="watermark_settings")]]))
    await m.answer()


@Client.on_callback_query(filters.regex(r"^give_access"))
async def give_access_handler(c: Client, query: CallbackQuery):
    try:
        if Config.IS_PRIVATE:
            user_id = int(query.data.split("#")[1])
            user = await get_user(user_id)
            if user["has_access"] and is_user_verified(user_id):
                return query.answer("User already have access", show_alert=True)
            await update_user_info(user_id, {"has_access": True, "last_verified": datetime.now()})
            await query.edit_message_text("User has been accepted successfully")
            return await c.send_message(user_id, f"You have been authenticated by Admin. Now you can use this bot for {Config.VERIFIED_TIME} days. Hit /help for more information")
        else:
            query.answer("Bot is Public", show_alert=True)
    except Exception as e:
        logging.exception(e, exc_info=True)


@Client.on_callback_query(filters.regex(r"^deny_access"))
async def deny_access_handler(c: Client, query: CallbackQuery):
    if Config.IS_PRIVATE:
        user_id = int(query.data.split("#")[1])
        user = await get_user(user_id)
        await update_user_info(user_id, {"has_access": False})
        await query.edit_message_text("User has been rejected successfully")
        return await c.send_message(user_id, "Your request has been rejected by Admin to use this bot.")
    else:
        query.answer("Bot is Public", show_alert=True)


@Client.on_callback_query(filters.regex(r"^request_access"))
async def request_access_handler(c: Client, query: CallbackQuery):
    try:
        if Config.IS_PRIVATE:
            user_id = int(query.data.split("#")[1])
            user = await get_user(user_id)
            if user["has_access"] and await is_user_verified(user_id=user_id):
                return await query.message.reply("You already have access to this Bot")
            REPLY_MARKUP = InlineKeyboardMarkup([[InlineKeyboardButton('Allow', callback_data=f'give_access#{query.from_user.id}'), InlineKeyboardButton(
                'Deny', callback_data=f'deny_access#{query.from_user.id}'), ], [InlineKeyboardButton('Close', callback_data='delete')]])

            await c.send_message(Config.LOG_CHANNEL, f"""
#NewRequest

User ID: {user_id}""", reply_markup=REPLY_MARKUP)
            await query.edit_message_text("Request has been sent to Admin. You will be notified when Admin accepts your request")
        else:
            query.answer("Bot is Public", show_alert=True)
    except Exception as e:
        logging.exception(e, exc_info=True)


@Client.on_callback_query()
async def on_callback_query(bot: Client, query: CallbackQuery):
    user_id = query.from_user.id
    h = Helpers()
    user = await get_user(user_id)
    if query.data == 'delete':
        await query.message.delete()

    elif query.data == 'help_command':
        await query.message.edit(Config.HELP_MESSAGE.format(
            firstname=temp.FIRST_NAME,
            username=temp.BOT_USERNAME,
            repo=Config.SOURCE_CODE,
            owner="@ask_admin001"), reply_markup=HELP_REPLY_MARKUP, disable_web_page_preview=True)

    elif query.data == 'about_command':
        bot = await bot.get_me()
        await query.message.edit(Config.ABOUT_TEXT.format(bot.mention(style='md')), reply_markup=ABOUT_REPLY_MARKUP, disable_web_page_preview=True)

    elif query.data == 'start_command':
        START_MESSAGE_REPLY_MARKUP = InlineKeyboardMarkup([[InlineKeyboardButton('Help', callback_data='help_command'), InlineKeyboardButton('About', callback_data='about_command')], [InlineKeyboardButton(
            'Method', callback_data='method_command'), InlineKeyboardButton('Join Channel♥️', url=f'https://telegram.me/{Config.USERNAME}')], [InlineKeyboardButton('Close', callback_data='delete')]])
        new_user = await get_user(query.from_user.id)
        tit = Config.START_MESSAGE.format(
            query.from_user.mention, new_user["method"], new_user["base_site"])
        await query.message.edit(tit, reply_markup=START_MESSAGE_REPLY_MARKUP, disable_web_page_preview=True)

    elif query.data.startswith('change_method'):
        method_name = query.data.split('#')[1]
        user = temp.BOT_USERNAME
        await update_user_info(user_id, {"method": method_name})
        REPLY_MARKUP = InlineKeyboardMarkup(
            [[InlineKeyboardButton('Back', callback_data='method_command')]])
        await query.message.edit("Method changed successfully to `{method}`".format(method=method_name, username=user), reply_markup=REPLY_MARKUP)

    elif query.data.startswith('change_site'):
        _, site = query.data.split('#')
        if site in Config.base_sites:
            await update_user_info(user_id, {"base_site": site})
            site_index = Config.base_sites.index(site) + 1
            user = await get_user(user_id)
            if user[f'shortener_api_{site_index}']:
                await update_user_info(user_id, {"shortener_api": user[f'shortener_api_{site_index}']})
                return await query.message.edit("Base Site Updated Sucessfully. Start sending posts",)
            REPLY_MARKUP = InlineKeyboardMarkup(
                [[InlineKeyboardButton(site, url=f'https://{site}/member/tools/api')]])
            await query.message.edit(f"There is no API found for {site}. Send your api from or Click the below button to connect", reply_markup=REPLY_MARKUP)
        else:
            await query.message.edit("This website is not available")

    elif query.data.startswith('change_font'):
        _, font = query.data.split('#')
        user_id = query.from_user.id
        await update_user_info(user_id, {"font": font})
        await query.answer("Updated Successfully", show_alert=1)
        user = await get_user(user_id)
        font = user["font"]
        text = f"Current Font: {Config.font_dict.get(font)}"
        await query.edit_message_text(text, reply_markup=query.message.reply_markup)

    elif query.data == 'method_command':
        s = Config.METHOD_MESSAGE.format(
            method=user["method"], shortener=user["base_site"],)

        if Config.IS_MDISK:
            method_btn = [[InlineKeyboardButton('Mdisk+shortner', callback_data='change_method#mdlink'), InlineKeyboardButton('Shortener', callback_data='change_method#shortener'), InlineKeyboardButton(
                'Mdisk', callback_data='change_method#mdisk')], [InlineKeyboardButton('Back', callback_data='help_command'), InlineKeyboardButton('Close', callback_data='delete')]]
        else:
            method_btn = [[InlineKeyboardButton('Mdisk+Shortner', callback_data='change_method#mdlink'), InlineKeyboardButton('Shortener', callback_data='change_method#shortener')], [
                InlineKeyboardButton('Back', callback_data='help_command'), InlineKeyboardButton('Close', callback_data='delete')]]

        METHOD_REPLY_MARKUP = InlineKeyboardMarkup(method_btn)

        return await query.message.edit(s, reply_markup=METHOD_REPLY_MARKUP)

    elif query.data == 'cbatch_command':
        if user_id not in Config.ADMINS:
            return await query.message.edit("Works only for admins", reply_markup=BACK_REPLY_MARKUP)

        await query.message.edit(Config.BATCH_MESSAGE, reply_markup=BACK_REPLY_MARKUP)

    elif query.data == 'alias_conf':
        await query.message.edit(Config.CUSTOM_ALIAS_MESSAGE, reply_markup=BACK_REPLY_MARKUP, disable_web_page_preview=True)

    elif query.data == 'admins_list':
        if user_id not in Config.ADMINS:
            return await query.message.edit("Works only for admins", reply_markup=BACK_REPLY_MARKUP)

        await query.message.edit(Config.ADMINS_MESSAGE.format(
            admin_list=await h.get_admins
        ), reply_markup=BACK_REPLY_MARKUP)

    elif query.data == 'channels_list':
        if user_id not in Config.ADMINS:
            return await query.message.edit("Works only for admins", reply_markup=BACK_REPLY_MARKUP)

        await query.message.edit(Config.CHANNELS_LIST_MESSAGE.format(
            channels=await h.get_channels
        ), reply_markup=BACK_REPLY_MARKUP)

    elif query.data == 'restart':
        await query.message.edit('**Restarting.....**')
        await asyncio.sleep(5)
        os.execl(sys.executable, sys.executable, *sys.argv)

    await query.answer()
