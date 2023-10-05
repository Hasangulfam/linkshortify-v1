# temp db for banned

import database
from config import Config
import asyncio
import logging
import aiohttp
import traceback


class temp(object):  # Eva Maria Idea of Temping
    BOT_USERNAME = None
    CANCEL = False
    FIRST_NAME = None
    START_TIME = None
    DB_CHANNEL = None


class AsyncIter:
    def __init__(self, items):
        self.items = items

    async def __aiter__(self):
        for item in self.items:
            yield item

    async def __anext__(self):
        try:
            return next(self.iter)
        except StopIteration:
            raise StopAsyncIteration


class Helpers:
    def __init__(self):
        self.username = temp.BOT_USERNAME

    @property
    async def user_mdisk_api(self):
        return Config.MDISK_API

    @property
    async def user_droplink_api(self):
        return Config.DROPLINK_API

    @property
    async def user_method(self):
        user_method = await database.db.get_bot_method(self.username)
        return user_method or "None"

    @property
    async def get_included_domain(self):
        if Config.INCLUDE_DOMAIN:
            x = ''
            async for i in AsyncIter(Config.INCLUDE_DOMAIN):
                x += f"- `{i}`"
            return x
        return "No Included Domain"

    @property
    async def get_excluded_domain(self):
        if Config.EXCLUDE_DOMAIN:
            x = ''
            async for i in AsyncIter(Config.EXCLUDE_DOMAIN):
                x += f"- `{i}`\n"
            return x
        return "No Excluded Domain"

    @property
    async def get_channels(self):
        if Config.CHANNELS:
            x = ''
            async for i in AsyncIter(Config.CHANNEL_ID):
                x += f"~ `{i}`\n"
            return x
        return "Channels is set to False in heroku Var"

    @property
    async def get_admins(self):
        x = ''
        async for i in AsyncIter(Config.ADMINS):
            x += f"~ `{i}`\n"
        return x

    @property
    async def header_text(self):
        return Config.HEADER_TEXT or "No Header Text"

    @property
    async def footer_text(self):
        return Config.FOOTER_TEXT or "No Footer Text"

    @property
    async def get_username(self):
        return Config.USERNAME


async def ping_server():
    sleep_time = Config.PING_INTERVAL
    while True:
        await asyncio.sleep(sleep_time)
        try:
            async with aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=10)
            ) as session:
                async with session.get(Config.REPLIT) as resp:
                    logging.info(f"Pinged server with response: {resp.status}")
        except TimeoutError:
            logging.warning("Couldn't connect to the site URL..!")
        except Exception:
            traceback.print_exc()
