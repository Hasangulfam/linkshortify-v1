import os
from dotenv import load_dotenv

load_dotenv()


def is_enabled(value, default):
    if value.lower() in ["true", "yes", "1", "enable", "y"]:
        return True
    elif value.lower() in ["false", "no", "0", "disable", "n"]:
        return False
    else:
        return default


class Config(object):
    # Mandatory variables for the bot to start
    API_ID = int(os.environ.get("API_ID", "26726762"))
    API_HASH = os.environ.get("API_HASH", "04c1514942a1fa624c461d1b0d61b85a")
    BOT_TOKEN = os.environ.get("BOT_TOKEN", "6423894289:AAEOJtMi95CxKd8oF_msQxd7uVDvuEdghBw")
    DROPLINK_API = os.environ.get("DROPLINK_API")
    MDISK_API = os.environ.get("MDISK_API")
    ADMINS = ["399726799"]
    DATABASE_NAME = os.environ.get("DATABASE_NAME", "MdiskConvertor")
    DATABASE_URL = os.environ.get("DATABASE_URL", "mongodb+srv://hasangulfam:GULfam6512@cluster0.egyrz70.mongodb.net/?retryWrites=true&w=majority")
    OWNER_ID = int(os.environ.get("OWNER_ID", "1252654109"))

    #  Optionnal variables
    BROADCAST_AS_COPY = False
    IS_PRIVATE = False
    INCLUDE_DOMAIN = []
    EXCLUDE_DOMAIN = []
    CHANNELS = True
    CHANNEL_ID = [-1001654232839]
    FORWARD_MESSAGE = False
    SOURCE_CODE = ""
    USERNAME = None
    HASHTAG = None
    HEADER_TEXT = ""
    FOOTER_TEXT = ""
    BANNER_IMAGE = ""
    WELCOME_IMAGE = "https://telegra.ph/file/ecec58a3b9a41ba8c2d4a.jpg"
    LINK_BYPASS = False

    FONT_DIR = "fonts"

    #  Heroku Config
    HEROKU_API_KEY = os.environ.get("HEROKU_API_KEY", None)
    HEROKU_APP_NAME = os.environ.get("HEROKU_APP_NAME", None)
    HEROKU = bool(HEROKU_API_KEY and HEROKU_APP_NAME and "DYNOS" in os.environ)

    #  Replit Config
    REPLIT_USERNAME = os.environ.get("REPLIT_USERNAME", None)
    REPLIT_APP_NAME = os.environ.get("REPLIT_APP_NAME", None)
    REPLIT = (
        f"https://{REPLIT_APP_NAME.lower()}.{REPLIT_USERNAME}.repl.co"
        if REPLIT_APP_NAME and REPLIT_USERNAME
        else False
    )
    PING_INTERVAL = int(os.environ.get("PING_INTERVAL", "300"))

    MAINTENENCE_MODE = False

    VERIFIED_TIME = 1
    LOG_CHANNEL = "-1001747405550"
    UPDATE_CHANNEL: int = 0
    KEYBOARD_BUTTON = True

    IS_MDISK = True
    IS_DEFAULT_BASE_SITE = True
    FILE_STORE_DB = -1001589836058
    FILE_STORE_BOT_USERNAME = "gyanilinksfilesharingbot"
    FILE_STORE = bool(FILE_STORE_DB and FILE_STORE_BOT_USERNAME)

    DIRECT_GEN_DB = -1001589836058
    DIRECT_GEN_BOT_USERNAME = "gyanilinkfilestreambot"
    DIRECT_GEN_URL = "143.244.137.54"
    DIRECT_GEN = bool(DIRECT_GEN_DB and DIRECT_GEN_BOT_USERNAME and DIRECT_GEN_URL)

    IS_BINDASSLINKS = True
    IS_DROPLINK = True
    IS_TNLINKS = True
    IS_INDIANSHORTENER = True
    IS_EASYSKY = True
    IS_LINKSHORTIFY = True
    IS_EARNL_SITE = True
    IS_EARNL_XYZ = True
    IS_URLEARN_XYZ = True
    KEEP_ALIVE = False

    stream_msg_text = """
<u>**Successfully Generated Your Link !**</u>\n
<b>📂 File Name :</b> {}\n
<b>📦 File Size :</b> {}\n"""

    BASE_SITE = os.environ.get("BASE_SITE", "gyanilinks.com")
    BASE_SITE_2 = os.environ.get("BASE_SITE_2", None)
    BASE_SITE_3 = os.environ.get("BASE_SITE_3", None)

    base_sites = [i for i in [BASE_SITE, BASE_SITE_2, BASE_SITE_3] if i != None]

    font_dict = {
        "bold": "<b>Text</b>",
        "italic": "<i>Text</i>",
        "strike": "<s>Text</s>",
        "underline": "<u>Text</u>",
        "spoiler": "<spoiler>Text</spoiler>",
    }
