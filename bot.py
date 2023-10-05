import datetime
import asyncio
import sys
from pyrogram import Client
import pyromod
from config import Config
from database import db
from helpers import temp
from utils import _update_existing_users, _update_existing_vars, broadcast_admins, make_vars

from flask import Flask, jsonify
from threading import Thread

import logging
import logging.config

# Get logging configurations
logging.config.fileConfig('logging.conf')
logging.getLogger().setLevel(logging.INFO)


app = Flask('')


@app.route('/')
def main():
    res = {
        "status": "running",
    }
    return jsonify(res)


def run():
    app.run(host="0.0.0.0", port=8000)


async def keep_alive():
    server = Thread(target=run)
    server.start()


class Bot(Client):

    def __init__(self):
        super().__init__(
            "shortener",
            api_id=Config.API_ID,
            api_hash=Config.API_HASH,
            bot_token=Config.BOT_TOKEN,
            plugins=dict(root="plugins")
        )

    async def start(self):

        if Config.KEEP_ALIVE:
            await keep_alive()

        temp.START_TIME = datetime.datetime.now()
        await super().start()
        me = await self.get_me()
        self.username = f'@{me.username}'
        temp.BOT_USERNAME = me.username
        temp.FIRST_NAME = me.first_name

        None if await db.get_bot_stats() else await db.create_stats()
        None if await db.get_bot_vars() else await db.create_vars()

        # update col for existing users
        await _update_existing_users()

        # update existing vars
        await _update_existing_vars()

        # set vars
        await make_vars()

        if Config.FILE_STORE:
            try:
                db_channel = await self.get_chat(Config.FILE_STORE_DB)
                temp.DB_CHANNEL = db_channel
                test = await self.send_message(chat_id=db_channel.id, text="Test Message")
                await test.delete()
            except Exception as e:
                logging.error(e)
                sys.exit()

        await broadcast_admins(self, '** Bot started successfully **')
        logging.info('Bot started')
        logging.info(f"Diect Link Gen - {Config.DIRECT_GEN}")

    async def stop(self, *args):
        await broadcast_admins(self, '** Bot Stopped Bye **')
        await super().stop()
        logging.info('Bot Stopped Bye')
