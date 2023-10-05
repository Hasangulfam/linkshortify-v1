import functools

from config import Config
from pyrogram import Client
from pyrogram.types import Message


def maintenence_mode(func):
    @functools.wraps(func)
    async def wrapper(client: "Client", message: "Message"):

        if Config.MAINTENENCE_MODE and message.from_user.id not in Config.ADMINS:
            return await message.reply_text("**🛠 Guys Bot Is Under Maintenance 🛠\n\n⚙ Developers Are Working On Bot ⚙\n\n✅ When Bot Will Be Ready We Will Inform You**", quote=True)
            
        return await func(client, message)
    return wrapper
