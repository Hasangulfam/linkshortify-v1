from config import Config
from motor.motor_asyncio import AsyncIOMotorClient
import helpers
from translation import *

class Database:
    def __init__(self, uri, database_name):
        self._client = AsyncIOMotorClient(uri)
        self.db = self._client[database_name]
        self.method = self.db['methods']
        self.stats = self.db['stats']
        self.misc = self.db["misc"]
        self.vars = self.db['vars']

    async def get_db_size(self):
        return (await self.db.command("dbstats"))['dataSize']
    
    async def get_bot_stats(self):
        return await self.stats.find_one({"bot": helpers.temp.BOT_USERNAME})

    async def create_stats(self):
        await self.stats.insert_one({
            'bot': helpers.temp.BOT_USERNAME,
            'posts': 0,
            'links': 0,
            'mdisk_links': 0,
            'shortener_links': 0
        })

    async def update_posts(self, posts:int):
        myquery = {"bot": helpers.temp.BOT_USERNAME,}
        newvalues = { "$inc": { "posts": posts } }
        return await self.stats.update_one(myquery, newvalues)

    async def update_links(self, links:int, droplink:int=0, mdisk:int=0):
        myquery = {"bot": helpers.temp.BOT_USERNAME,}
        newvalues = { "$inc": { "links": links ,  'mdisk_links': mdisk, 'shortener_links': droplink} }
        return await self.stats.update_one(myquery, newvalues)

    async def create_vars(self):
        await self.vars.insert_one({
            'bot': helpers.temp.BOT_USERNAME,
            'admins': [],
            'broadcast_as_copy':False,
            'is_private': False,
            'channels':False,
            'channel_id': [],
            'source_code':'',
            'username':None,
            'hashtag':None,
            'header_text':None,
            'footer_text':None,
            'banner_image':None,
            'welcome_image':None,
            'link_bypass':False,
            'base_site':Config.BASE_SITE,
            'verified_time':1,
            'log_channel':0,
            'update_channel':0,
            'keyboard_button':False,
            'is_mdisk':False,
            'is_default_base_site':False,
            'file_store_db':0,
            'file_store_bot_username':'',
            'direct_gen_db':0,
            'direct_gen_bot_username':'',
            'direct_gen_url':'',
            'is_bindasslinks':False,
            'is_droplink':False,
            'is_tnlinks':False,
            'is_indianshortener':False,
            'is_easysky':False,
            'is_earnl_site':False,
            'is_earnl_xyz':False,
            'is_urlearn_xyz':False,
            'is_linkshortify':False,
            'base_site_2':Config.BASE_SITE_2,
            'base_site_3':Config.BASE_SITE_3,
            'start_message':Config.START_MESSAGE,
            'help_message':Config.HELP_MESSAGE,
            'about_message':Config.ABOUT_TEXT,
            'method_message':Config.METHOD_MESSAGE,
            'user_about_message':Config.USER_ABOUT_MESSAGE,
            'mdisk_api_message':Config.MDISK_API_MESSAGE,
            'shortener_api_message':Config.SHORTENER_API_MESSAGE,
            'username_message':Config.USERNAME_TEXT,
            'hashtag_message':Config.HASHTAG_TEXT,
            'pvt_links_message':Config.PVT_LINKS_TEXT,
            'banner_image_message':Config.BANNER_IMAGE_TEXT,
            'include_domain_message':Config.INCLUDE_DOMAIN_TEXT,
            'exclude_domain_message':Config.EXCLUDE_DOMAIN_TEXT,
            'bitly_api_message':Config.BITLY_API_MESSAGE,
            'features_message':Config.FEATURES_MESSAGE,
            'balance_message':Config.BALANCE_CMD_TEXT,
            'account_message':Config.ACCOUNT_CMD_TEXT,
            'header_message':Config.HEADER_MESSAGE,
            'shortener_api_message':Config.SHORTENER_API_MESSAGE,
            'footer_message':Config.FOOTER_MESSAGE,
            'join_channel_username':Config.USERNAME
        })

    async def get_bot_vars(self):
        return (await self.vars.find_one({"bot": helpers.temp.BOT_USERNAME}))

    async def update_bot_vars(self, value:dict):
        print(helpers.temp.BOT_USERNAME)
        myquery = {"bot": helpers.temp.BOT_USERNAME}
        newvalues = {"$set" : value}
        return await self.vars.update_one(myquery, newvalues)


db = Database(Config.DATABASE_URL, Config.DATABASE_NAME)
