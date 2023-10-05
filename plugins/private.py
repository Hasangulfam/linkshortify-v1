import logging

from config import Config
from database.users import get_user, is_user_verified, update_user_info
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message
from utils import extract_link, main_convertor_handler, update_stats, user_api_check

logger = logging.getLogger(__name__)

print(__name__)


#
@Client.on_message(filters.private & filters.incoming)
async def private_link_main_handler(c: Client, message: Message):
    print("Message Received")
    user = await get_user(message.from_user.id)
    out = await message.reply_text("Loading . . .")
    try:
        user["is_pvt_link"]
    except KeyError:
        await update_user_info(
            message.from_user.id, {"pvt_link": None, "is_pvt_link": False}
        )

    try:
        if message.text:
            has_link = len(await extract_link(message.text))
            api = message.text.replace(" ", "").replace("  ", "")
            if message.text.startswith("/"):
                return await out.edit("Please send a valid link")

            elif len(api) == 20 and has_link <= 0 and not message.reply_markup:
                await update_user_info(message.from_user.id, {"mdisk_api": api})
                return await out.edit(f"Mdisk API updated successfully to {api}")

            elif len(api) == 40 and has_link <= 0 and not message.reply_markup:
                await update_user_info(message.from_user.id, {"shortener_api": api})
                site_index = Config.base_sites.index(user["base_site"]) + 1
                await update_user_info(
                    message.from_user.id, {f"shortener_api_{site_index}": api}
                )
                return await out.edit(f"Shortener API updated successfully to {api}")

        # User Verification
        has_access = (await get_user(message.from_user.id))["has_access"]

        REPLY_MARKUP = InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton(
                        "Request Access",
                        callback_data=f"request_access#{message.from_user.id}",
                    ),
                ],
            ]
        )
        if (
            message.from_user.id not in Config.ADMINS
            and Config.IS_PRIVATE
            and not has_access
        ):
            return await out.edit(
                "This bot works only for authorized users. Request admin to use this bot",
                reply_markup=REPLY_MARKUP,
            )

        is_verified = await is_user_verified(message.from_user.id)

        if not is_verified and has_access:
            REPLY_MARKUP = InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton(
                            "Request Access",
                            callback_data=f"request_access#{message.from_user.id}",
                        ),
                    ],
                ]
            )
            return out.edit(
                f"Your Verification time has expired. Request admin to use this bot",
                reply_markup=REPLY_MARKUP,
            )

        user_method = user["method"]

        vld = await user_api_check(user)

        if vld is not True:
            return await out.edit(vld)

        try:
            txt = await out.edit("`🔗 Cooking Your Links So Please Wait . . . `")
            await main_convertor_handler(message, user_method, user=user)

            if message.caption:
                await update_stats(message, user_method)

        except Exception as e:
            await out.edit(f"Error while trying to convert links {e}:")
            logger.exception(e, exc_info=True)
        finally:
            await txt.delete()

    except Exception as e:
        logger.exception(e, exc_info=True)
