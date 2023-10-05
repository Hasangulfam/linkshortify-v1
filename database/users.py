from datetime import datetime
from motor.motor_asyncio import AsyncIOMotorClient
from config import Config

client = AsyncIOMotorClient(Config.DATABASE_URL)
db = client[Config.DATABASE_NAME]
col = db["users"]
misc = db["misc"]


async def get_user(user_id):
    user_id = int(user_id)
    user = await col.find_one({"user_id": user_id})
    if not user:
        res = {
            "user_id": user_id,
            "method": "shortener",
            "shortener_api_1": None,
            "shortener_api_2": None,
            "shortener_api_3": None,
            "shortener_api": None,
            "mdisk_api": None,
            "header_text": "",
            "footer_text": "",
            "username": None,
            "base_site": Config.BASE_SITE,
            "banner_image": None,
            "hashtag": None,
            "bitly_api": None,
            "font": None,
            "pvt_link": None,
            "is_pvt_link": True,
            "is_bitly_link": False,
            "is_banner_image": True,
            "is_username": True,
            "is_hashtag": True,
            "is_font": True,
            "is_header_text": True,
            "is_footer_text": True,
            "include_domain": [],
            "exclude_domain": [],
            "has_access": False,
            "watermark": {
                "watermark_color": "white",
                "status": True,
                "watermark_text": None,
                "watermark_position": ("center", "center"),
                "watermark_size": 50,
                "watermark_font": "Helvetica-Bold",
                "watermark_opacity": 1.0
            },
            "forward_channels": {"status": False, "channels": []},
            "last_verified": datetime(2020, 5, 17),
        }

        await col.insert_one(res)
        user = await col.find_one({"user_id": user_id})
    return user


async def update_user_info(user_id, value: dict):
    user_id = int(user_id)
    myquery = {"user_id": user_id}
    newvalues = {"$set": value}
    await col.update_one(myquery, newvalues)


async def total_users_count():
    return await col.count_documents({})


async def get_all_users():
    return col.find({})


async def delete_user(user_id):
    await col.delete_one({'user_id': int(user_id)})


async def update_verify_user(user_id, value: dict):
    user_id = int(user_id)
    await get_user(user_id)
    myquery = {"user_id": user_id}
    newvalues = {"$set": value}
    await misc.update_one(myquery, newvalues)


async def is_user_verified(user_id):
    user = await get_user(user_id)
    try:
        pastDate = user["last_verified"]
    except Exception:
        user = await get_user(user_id)
        pastDate = user["last_verified"]
    return (datetime.now() - pastDate).days <= Config.VERIFIED_TIME


async def total_users_count():
    return await col.count_documents({})


async def is_user_exist(id):
    user = await col.find_one({'user_id': int(id)})
    return bool(user)


async def update_existing_users(filter, update):
    return await col.update_many(filter=filter, update=update)


async def remove_user_forward_channel(user_id, channel_id):
    user = await get_user(user_id)
    forward_channels = user["forward_channels"]["channels"]
    forward_channels.remove(channel_id)
    status = user["forward_channels"]["status"]
    await update_user_info(user_id, {"forward_channels": {"status": status, "channels": forward_channels}})


async def add_user_forward_channel(user_id, channel_id):
    user = await get_user(user_id)
    forward_channels = user["forward_channels"]["channels"]
    forward_channels.append(channel_id)
    status = user["forward_channels"]["status"]
    await update_user_info(user_id, {"forward_channels": {"status": status, "channels": forward_channels}})
