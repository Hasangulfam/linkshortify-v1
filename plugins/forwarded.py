import logging

from config import Config
from database.users import get_user
from pyrogram import Client, filters
from utils import (broadcast_admins, main_convertor_handler, update_stats,
                   user_api_check)

logger = logging.getLogger(__name__)
logger.setLevel(logging.ERROR)


# edit forwarded message
@Client.on_message(filters.chat(Config.CHANNEL_ID) & (
        filters.channel | filters.group) & filters.incoming & ~filters.private & filters.forwarded)
async def channel_forward_link_handler(c:Client, message):
    
    user = await get_user(message.from_user.id)
    user_method = user["method"]

    vld = await user_api_check(user)

    if vld is not True and Config.CHANNELS: return await broadcast_admins(c, "To use me in channel...\n\n" + vld )

    if Config.FORWARD_MESSAGE and Config.CHANNELS :
        try:
            await main_convertor_handler(message, user_method)
            await message.delete()
            # Updating DB stats
            await update_stats(message, user_method)

        except Exception as e:
            logger.error(e)
