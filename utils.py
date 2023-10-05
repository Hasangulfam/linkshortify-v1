import asyncio
import base64
import fnmatch
import os
import random
import re
import json
import time
import aiohttp
import contextlib
import heroku3
from pyrogram import Client, enums
import webcolors
from database import db
import requests
from pyrogram.raw.types.messages import Messages
from shortzy import Shortzy
from mdisky import Mdisk
from bs4 import BeautifulSoup
from urllib.parse import urlparse
from pyrogram.errors import FloodWait
from config import Config
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, InputMediaPhoto
import pyshorteners
from pyrogram.errors.exceptions.bad_request_400 import PeerIdInvalid
import logging
from urllib.parse import quote_plus
from database.users import get_user, update_existing_users, update_user_info
from PIL import Image, ImageDraw, ImageFont
from helpers import temp

logger = logging.getLogger(__name__)
logger.setLevel(logging.ERROR)


async def main_convertor_handler(
    message: Message, type: str, edit_caption: bool = False, user=None
):
    username = Config.USERNAME
    hashtag = Config.HASHTAG
    header_text = Config.HEADER_TEXT
    footer_text = Config.FOOTER_TEXT
    banner_image = Config.BANNER_IMAGE

    if user:
        header_text = user["header_text"] if user["is_header_text"] else ""
        footer_text = user["footer_text"] if user["is_footer_text"] else ""
        hashtag = user["hashtag"] if user["is_hashtag"] else None
        username = user["username"] if user["is_username"] else None
        banner_image = user["banner_image"] if user["is_banner_image"] else None
        pvt_link = user["pvt_link"] if user["is_pvt_link"] else None
        font = user["font"] if user["is_font"] else None

    caption = None

    if message.text:
        caption = message.text.html
    elif message.caption:
        caption = message.caption.html

    # Checking if the message has any link or not. If it doesn't have any link, it will return.
    if (
        caption and len(await extract_link(caption)) <= 0 and not message.reply_markup
    ) or not caption:
        return

    user_method = type

    # Checking if the user has set his method or not. If not, it will reply with a message.
    if user_method is None:
        return await message.reply(text="Set your /method first")

    # Bypass Links
    caption = await droplink_bypass_handler(caption)
    # A dictionary which contains the methods to be called.
    METHODS = {
        "mdisk": mdisk_api_handler,
        "shortener": replace_link,
        "mdlink": mdisk_droplink_convertor,
    }

    # Replacing the username with your username.
    caption = await replace_username(caption, username)
    # Replacing the hashtag with your hashtag.
    caption = await replace_hashtag(caption, hashtag)

    # Replacing the private links with your links.
    if pvt_link:
        caption = await replace_username(caption, pvt_link, is_pvt_links=True)

    # Getting the function for the user's method
    method_func = METHODS[user_method]

    # converting urls
    shortenedText = await method_func(user, caption)

    # converting reply_markup urls
    reply_markup = await reply_markup_handler(message, method_func)

    try:
        shortenedText = (
            await bitly_short_handler(shortenedText, user)
            if user["is_bitly_link"] and user["bitly_api"]
            else shortenedText
        )
    except Exception as e:
        logging.error(e)

    # Adding header and footer
    shortenedText = f"{header_text}\n{shortenedText}\n{footer_text}"

    # font change
    font = (
        Config.font_dict.get(font, "Text").replace("Text", "{text}")
        if font
        else "{text}"
    )
    shortenedText = font.format(text=shortenedText)

    # applying watermark
    if user["watermark"] and user["watermark"]["watermark_text"] and user["watermark"]["status"] and message.media and message.photo:
        watermark_text = user["watermark"]["watermark_text"]
        font_path = user["watermark"]["watermark_font"]
        watermark_fontsize = user["watermark"]["watermark_size"]
        watermark_opacity = user["watermark"]["watermark_opacity"]
        watermark_color = user["watermark"]["watermark_color"]
        watermark_position = user["watermark"]["watermark_position"]
        image = banner_image
        if not image:
            path = f"downloads/{message.id}-{message.chat.id}.png"
            image = await message.download(path)
        else:
            image = await download_image(image, "downloads")
        font_path = await search_file(Config.FONT_DIR, f"{font_path}")
        res = await apply_watermark(
            image,
            watermark_text,
            font_path,
            watermark_fontsize,
            watermark_color,
            watermark_opacity,
            watermark_position,
        )
        res.save(image, "PNG")
        banner_image = image

    if message.media and message.photo:
        medias = getattr(message, message.media.value)
        fileid = medias.file_id
        if banner_image:
            fileid = banner_image
        if edit_caption:
            fileid = InputMediaPhoto(banner_image, caption=shortenedText)

    if message.chat.type == enums.ChatType.PRIVATE and not user["forward_channels"]["status"]:
        if reply_markup:
            # add a button to the reply_markup
            reply_markup["inline_keyboard"].append(
                [
                    InlineKeyboardButton(
                        text="Forward", callback_data="forward_post#{}".format(message.from_user.id)
                    )
                ]
            )
        else:
            reply_markup = InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton(
                            text="Forward", callback_data="forward_post#{}".format(message.from_user.id)
                        )
                    ]
                ]
            )

    if message.text:
        if user_method in {"shortener", "mdlink"} and "|" in caption:
            regex = r"(?i)\b((?:https?://|www\d{0,3}[.]|[a-z0-9.\-]+[.][a-z]{2,4}/)(?:[^\s()<>]+|\(([^\s()<>]+|(\([^\s()<>]+\)))*\))+(?:\(([^\s()<>]+|(\([^\s()<>]+\)))*\)|[^\s`!()\[\]{};:'\".,<>?«»“”‘’]))\s\|\s([a-zA-Z0-9_]){,30}"
            if custom_alias := re.match(regex, caption):
                custom_alias = custom_alias[0].split("|")
                alias = custom_alias[1].strip()
                url = custom_alias[0].strip()
                shortenedText = await method_func(user, url, alias)

        if edit_caption:
            return await message.edit(
                shortenedText, disable_web_page_preview=True, reply_markup=reply_markup
            )

        message = await message.reply(
            shortenedText,
            disable_web_page_preview=True,
            reply_markup=reply_markup,
            quote=True,
        )

    elif message.media:
        if edit_caption:
            if Config.BANNER_IMAGE and message.photo:
                return await message.edit_media(media=fileid)

            message = await message.edit_caption(shortenedText, reply_markup=reply_markup)

        if message.document:
            message = await message.reply_document(
                fileid, caption=shortenedText, reply_markup=reply_markup, quote=True
            )

        elif message.photo:
            message = await message.reply_photo(
                fileid, caption=shortenedText, reply_markup=reply_markup, quote=True
            )

        elif message.video:
            message = await message.reply_video(
                fileid, caption=shortenedText, reply_markup=reply_markup, quote=True
            )
    if message.chat.type == enums.ChatType.PRIVATE:
        channels = user["forward_channels"]["channels"]
        for channel in channels:
            try:
                await message.copy(channel, caption=message.caption.html, reply_markup=message.reply_markup)
            except Exception as e:
                print(e)
    if banner_image:
        os.remove(banner_image)


# Reply markup
async def reply_markup_handler(message: Message, method_func):
    if message.reply_markup:
        user = await get_user(message.from_user.id)
        reply_markup = json.loads(str(message.reply_markup))
        buttsons = []
        for markup in reply_markup["inline_keyboard"]:
            buttons = []
            for j in markup:
                text = j["text"]
                url = j["url"]
                url = await method_func(user, url)
                button = InlineKeyboardButton(text, url=url)
                buttons.append(button)
            buttsons.append(buttons)
        reply_markup = InlineKeyboardMarkup(buttsons)
        return reply_markup


async def mdisk_api_handler(user, text):
    api_key = user["mdisk_api"] if user else Config.MDISK_API
    mdisk = Mdisk(api_key)
    return await mdisk.convert_from_text(text)


async def replace_link(user, text, x=""):
    api_key = user["shortener_api"]
    base_site = user["base_site"]
    shortzy = Shortzy(api_key, base_site)
    links = await extract_link(text)
    for link in links:
        if link != user["pvt_link"]:
            long_url = link
            logging.info(f"Contverting {long_url}")

            if "http" in link or "https" in link:

                if user["include_domain"]:
                    include = user["include_domain"]
                    domain = [domain.strip() for domain in include]
                    if any(i in link for i in domain):
                        try:
                            short_link = await shortzy.convert(link, x)
                        except Exception:
                            short_link = await tiny_url_main(
                                await shortzy.get_quick_link(link)
                            )
                        text = text.replace(long_url, short_link)
                elif user["exclude_domain"]:
                    exclude = user["include_domain"]
                    domain = [domain.strip() for domain in exclude]
                    if all(i not in link for i in domain):
                        try:
                            short_link = await shortzy.convert(link, x)
                        except Exception:
                            short_link = await tiny_url_main(
                                await shortzy.get_quick_link(link)
                            )
                        text = text.replace(long_url, short_link)
                else:
                    try:
                        short_link = await shortzy.convert(link, x)
                    except Exception as e:
                        logging.exception(e)
                        short_link = await tiny_url_main(
                            await shortzy.get_quick_link(link)
                        )
                    text = text.replace(long_url, short_link)
    return text


####################  Mdisk and Droplink  ####################
async def mdisk_droplink_convertor(user, text, alias=""):
    links = await mdisk_api_handler(user, text)
    links = await replace_link(user, links, x=alias)
    return links


####################  Replace Username  ####################
async def replace_username(text, username, is_pvt_links=False):
    if username:
        telegram_link_regex = r"(?:https?://)?(?:www\.)?(?:t(?:elegram)?\.me|telegram\.org)/(?:[^\s/?\.<>]+)+/?"
        if is_pvt_links:
            pvt_links = re.findall(telegram_link_regex, text)
            for i in pvt_links:
                text = text.replace(i, username, 1)
        else:
            usernames = re.findall("([@][A-Za-z0-9_]+)", text)
            for i in usernames:
                text = text.replace(i, f"@{username}")
    return text


####################  Replace hashtag  ####################
async def replace_hashtag(text, hashtag):
    if hashtag:
        hashtags = re.findall("([#][A-Za-z0-9_]+)", text)
        for i in hashtags:
            text = text.replace(i, f"#{hashtag}")
    return text


#####################  Extract all urls in a string ####################
async def extract_link(string):
    regex = r"""(?i)\b((?:https?:(?:/{1,3}|[a-z0-9%])|[a-z0-9.\-]+[.](?:com|net|org|edu|gov|mil|aero|asia|biz|cat|coop|info|int|jobs|mobi|museum|name|post|pro|tel|travel|xxx|ac|ad|ae|af|ag|ai|al|am|an|ao|aq|ar|as|at|au|aw|ax|az|ba|bb|bd|be|bf|bg|bh|bi|bj|bm|bn|bo|br|bs|bt|bv|bw|by|bz|ca|cc|cd|cf|cg|ch|ci|ck|cl|cm|cn|co|cr|cs|cu|cv|cx|cy|cz|dd|de|dj|dk|dm|do|dz|ec|ee|eg|eh|er|es|et|eu|fi|fj|fk|fm|fo|fr|ga|gb|gd|ge|gf|gg|gh|gi|gl|gm|gn|gp|gq|gr|gs|gt|gu|gw|gy|hk|hm|hn|hr|ht|hu|id|ie|il|im|in|io|iq|ir|is|it|je|jm|jo|jp|ke|kg|kh|ki|km|kn|kp|kr|kw|ky|kz|la|lb|lc|li|lk|lr|ls|lt|lu|lv|ly|ma|mc|md|me|mg|mh|mk|ml|mm|mn|mo|mp|mq|mr|ms|mt|mu|mv|mw|mx|my|mz|na|nc|ne|nf|ng|ni|nl|no|np|nr|nu|nz|om|pa|pe|pf|pg|ph|pk|pl|pm|pn|pr|ps|pt|pw|py|qa|re|ro|rs|ru|rw|sa|sb|sc|sd|se|sg|sh|si|sj|Ja|sk|sl|sm|sn|so|sr|ss|st|su|sv|sx|sy|sz|tc|td|tf|tg|th|tj|tk|tl|tm|tn|to|tp|tr|tt|tv|tw|tz|ua|ug|uk|us|uy|uz|va|vc|ve|vg|vi|vn|vu|wf|ws|ye|yt|yu|za|zm|zw)/)(?:[^\s()<>{}\[\]]+|\([^\s()]*?\([^\s()]+\)[^\s()]*?\)|\([^\s]+?\))+(?:\([^\s()]*?\([^\s()]+\)[^\s()]*?\)|\([^\s]+?\)|[^\s`!()\[\]{};:'".,<>?«»“”‘’])|(?:(?<!@)[a-z0-9]+(?:[.\-][a-z0-9]+)*[.](?:com|net|org|edu|gov|mil|aero|asia|biz|cat|coop|info|int|jobs|mobi|museum|name|post|pro|tel|travel|xxx|ac|ad|ae|af|ag|ai|al|am|an|ao|aq|ar|as|at|au|aw|ax|az|ba|bb|bd|be|bf|bg|bh|bi|bj|bm|bn|bo|br|bs|bt|bv|bw|by|bz|ca|cc|cd|cf|cg|ch|ci|ck|cl|cm|cn|co|cr|cs|cu|cv|cx|cy|cz|dd|de|dj|dk|dm|do|dz|ec|ee|eg|eh|er|es|et|eu|fi|fj|fk|fm|fo|fr|ga|gb|gd|ge|gf|gg|gh|gi|gl|gm|gn|gp|gq|gr|gs|gt|gu|gw|gy|hk|hm|hn|hr|ht|hu|id|ie|il|im|in|io|iq|ir|is|it|je|jm|jo|jp|ke|kg|kh|ki|km|kn|kp|kr|kw|ky|kz|la|lb|lc|li|lk|lr|ls|lt|lu|lv|ly|ma|mc|md|me|mg|mh|mk|ml|mm|mn|mo|mp|mq|mr|ms|mt|mu|mv|mw|mx|my|mz|na|nc|ne|nf|ng|ni|nl|no|np|nr|nu|nz|om|pa|pe|pf|pg|ph|pk|pl|pm|pn|pr|ps|pt|pw|py|qa|re|ro|rs|ru|rw|sa|sb|sc|sd|se|sg|sh|si|sj|Ja|sk|sl|sm|sn|so|sr|ss|st|su|sv|sx|sy|sz|tc|td|tf|tg|th|tj|tk|tl|tm|tn|to|tp|tr|tt|tv|tw|tz|ua|ug|uk|us|uy|uz|va|vc|ve|vg|vi|vn|vu|wf|ws|ye|yt|yu|za|zm|zw)\b/?(?!@)))"""
    urls = re.findall(regex, string)
    return ["".join(x) for x in urls]


# Incase droplink server fails, bot will return https://droplink.co/st?api={DROPLINK_API}&url={link}

# TinyUrl
async def tiny_url_main(url):
    s = pyshorteners.Shortener()
    return s.tinyurl.short(url)


async def bitly_short(url, api):
    s = pyshorteners.Shortener(api_key=api)
    return s.bitly.short(url)


async def bitly_short_handler(text, user):
    api_key = user["bitly_api"]

    links = await extract_link(text)

    for link in links:
        long_url = link
        short_url = await bitly_short(long_url, api_key)
        text = text.replace(long_url, short_url)
    return text


# todo -> bypass long droplink url
async def droplink_bypass_handler(text):
    if Config.LINK_BYPASS:
        links = await extract_link(text)
        for link in links:
            if "bindaaslinks.com" in link and Config.IS_BINDASSLINKS:
                bypassed_link = await bindasslink_bypass(link)
            elif "droplink.co" in link and Config.IS_DROPLINK:
                bypassed_link = await droplink_bypass(link)
            elif "tnlink.in" in link and Config.IS_TNLINKS:
                bypassed_link = await tnlink_bypass(link)
            elif "easysky.in" in link and Config.IS_EASYSKY:
                bypassed_link = await easysky_bypass(link)
            elif "indianshortner" in link and Config.IS_INDIANSHORTENER:
                bypassed_link = await indianshortner_bypass(link)
            elif "lksfy" in link and Config.IS_LINKSHORTIFY:
                bypassed_link = await linkshortify_bypass(link)
            elif "earnl.site" in link and Config.IS_EARNL_SITE:
                bypassed_link = await earnl_site_bypass(link)
            elif "earnl.xyz" in link and Config.IS_EARNL_SITE:
                bypassed_link = await earnl_xyz_bypass(link)
            elif "vearnl.in" in link and Config.IS_URLEARN_XYZ:
                bypassed_link = await urlearn_xyz_bypass(link)
            with contextlib.suppress(Exception):
                text = text.replace(link, bypassed_link)
    return text


# credits -> https://github.com/TheCaduceus/Link-Bypasser
async def droplink_bypass(url):
    try:
        # client = aiohttp.ClientSession()
        async with aiohttp.ClientSession() as client:
            async with client.get(url) as res:
                ref = re.findall(
                    "action[ ]{0,}=[ ]{0,}['|\"](.*?)['|\"]", await res.text()
                )[0]
                h = {"referer": ref}
                # res = client.get(url, headers=h)
                async with client.get(url, headers=h) as res:
                    bs4 = BeautifulSoup(await res.content.read(), "html.parser")
                    inputs = bs4.find_all("input")
                    data = {input.get("name"): input.get("value")
                            for input in inputs}
                    h = {
                        "content-type": "application/x-www-form-urlencoded",
                        "x-requested-with": "XMLHttpRequest",
                    }
                    p = urlparse(url)
                    final_url = f"{p.scheme}://{p.netloc}/links/go"
                    await asyncio.sleep(3.1)
                    # res = client.post(final_url, data=data, headers=h).json()
                    async with client.post(final_url, data=data, headers=h) as res:
                        res = await res.json()
                        if res["status"] == "success":
                            return res["url"]
                        else:
                            raise Exception(
                                "Error while bypassing droplink {0}: {1}".format(
                                    url, res["message"]
                                )
                            )
    except Exception as e:
        raise Exception(e)


async def indianshortner_bypass(url):
    url = url.replace("https://indianshortner.in",
                      "https://indianshortner.com")
    try:
        h = {"referer": "https://moddingzone.in/"}
        client = requests.Session()
        res = client.get(url, headers=h)
        bs4 = BeautifulSoup(res.content, "lxml")
        inputs = bs4.find_all("input")
        data = {input.get("name"): input.get("value") for input in inputs}
        h = {
            "content-type": "application/x-www-form-urlencoded",
            "x-requested-with": "XMLHttpRequest",
            "referer": "url",
        }

        final_url = "https://indianshortner.com/links/go"
        time.sleep(5.1)
        res = client.post(final_url, data=data, headers=h).json()
        return res["url"]
    except Exception as e:
        raise Exception(e)


async def linkshortify_bypass(url):
    url = url.replace("https://lksfy.com", "https://linkshortify.site/")
    try:
        client = requests.Session()
        res = client.get(url, headers={"referer": "https://technoflip.in/"})
        bs4 = BeautifulSoup(res.content, "lxml")
        inputs = bs4.find_all("input")
        data = {input.get("name"): input.get("value") for input in inputs}
        h = {
            "content-type": "application/x-www-form-urlencoded",
            "x-requested-with": "XMLHttpRequest",
        }
        final_url = "https://linkshortify.site/links/go"
        time.sleep(int(os.environ.get("COUNTER_VALUE", "3")))
        res = client.post(final_url, data=data, headers=h).json()
        return res["url"]
    except Exception as e:
        print(e)


async def easysky_bypass(url):
    url = url.replace("https://m.easysky.in", "https://techy.veganab.co")
    try:
        h = {"referer": "https://veganab.co/"}
        client = requests.Session()
        res = client.get(url, headers=h)
        bs4 = BeautifulSoup(res.content, "lxml")
        inputs = bs4.find_all("input")
        data = {input.get("name"): input.get("value") for input in inputs}

        h = {
            "content-type": "application/x-www-form-urlencoded",
            "x-requested-with": "XMLHttpRequest",
        }

        final_url = "https://techy.veganab.co/links/go"
        time.sleep(5.1)
        res = client.post(
            final_url,
            data=data,
            headers=h,
        ).json()
        return res["url"]

    except Exception as e:
        raise Exception(
            "Error while bypassing droplink {0}: {1}".format(url, e)) from e


async def bindasslink_bypass(url):
    url = url.replace("https://bindaaslinks.com",
                      "https://www.thebindaas.com/blog/")

    try:
        h = {"referer": "https://www.thebindaas.com"}
        client = requests.Session()
        res = client.get(url, headers=h)
        bs4 = BeautifulSoup(res.content, "lxml")
        inputs = bs4.find_all("input")
        data = {input.get("name"): input.get("value") for input in inputs}
        h = {
            "content-type": "application/x-www-form-urlencoded",
            "x-requested-with": "XMLHttpRequest",
            "referer": url,
        }
        final_url = "https://www.thebindaas.com/blog/links/go"
        time.sleep(5.1)
        res = client.post(final_url, data=data, headers=h).json()
        print(res)
        return res["url"]
    except Exception as e:
        raise Exception(
            "Error while bypassing bindaaslinks {0}: {1}".format(url, e)) from e


async def earnl_site_bypass(url):
    url = url.replace("Go", "get")
    try:
        client = requests.Session()
        res = client.get(url, headers={"referer": "https://s.apkdone.live/"})
        bs4 = BeautifulSoup(res.content, "lxml")
        inputs = bs4.find_all("input")
        data = {input.get("name"): input.get("value") for input in inputs}
        h = {
            "content-type": "application/x-www-form-urlencoded",
            "x-requested-with": "XMLHttpRequest",
        }
        final_url = "https://get.earnl.site/links/go"
        time.sleep(int(os.environ.get("COUNTER_VALUE", "5")))
        res = client.post(final_url, data=data, headers=h).json()
        return res["url"]
    except Exception as e:
        print(e)


async def earnl_xyz_bypass(url):
    url = url.replace("go", "v")
    try:
        client = requests.Session()
        res = client.get(
            url, headers={"referer": "https://short.modmakers.xyz/"})
        bs4 = BeautifulSoup(res.content, "lxml")
        inputs = bs4.find_all("input")
        data = {input.get("name"): input.get("value") for input in inputs}
        h = {
            "content-type": "application/x-www-form-urlencoded",
            "x-requested-with": "XMLHttpRequest",
        }
        final_url = "https://v.earnl.xyz/links/go"
        time.sleep(int(os.environ.get("COUNTER_VALUE", "5")))
        res = client.post(final_url, data=data, headers=h).json()
        return res["url"]
    except Exception as e:
        print(e)


async def urlearn_xyz_bypass(url):
    url = url.replace("http://vearnl.in/", "https://go.urlearn.xyz/")
    try:
        client = requests.Session()
        res = client.get(
            url, headers={"referer": "https://download.modmakers.xyz/"})
        bs4 = BeautifulSoup(res.content, "lxml")
        inputs = bs4.find_all("input")
        data = {input.get("name"): input.get("value") for input in inputs}
        h = {
            "content-type": "application/x-www-form-urlencoded",
            "x-requested-with": "XMLHttpRequest",
        }
        final_url = "https://go.urlearn.xyz/links/go"
        time.sleep(int(os.environ.get("COUNTER_VALUE", "5")))
        res = client.post(final_url, data=data, headers=h).json()
        print(res)
        return res["url"]
    except Exception as e:
        print(e)


async def tnlink_bypass(url):
    url = url.replace("https://tnlink.in", "https://gadgets.usanewstoday.club")
    try:
        h = {"referer": "https://usanewstoday.club/"}
        client = requests.Session()
        res = client.get(url, headers=h)
        bs4 = BeautifulSoup(res.content, "lxml")
        inputs = bs4.find_all("input")
        data = {input.get("name"): input.get("value") for input in inputs}

        h = {
            "content-type": "application/x-www-form-urlencoded",
            "x-requested-with": "XMLHttpRequest",
            "referer": "url",
        }
        p = urlparse(url)
        final_url = "https://gadgets.usanewstoday.club/links/go"
        time.sleep(8.1)
        res = client.post(
            final_url,
            data=data,
            headers=h,
        ).json()
        return res["url"]

    except Exception as e:
        raise Exception(
            "Error while bypassing droplink {0}: {1}".format(url, e)) from e


async def is_droplink_url(url):
    domain = urlparse(url).netloc
    domain = url if "droplink.co" in domain else False
    return domain


async def broadcast_admins(c: Client, Message, sender=False):

    admins = Config.ADMINS[:]

    if sender:
        admins.remove(sender)

    for i in admins:
        try:
            await c.send_message(i, Message)
        except PeerIdInvalid:
            logging.info(f"{i} have not yet started the bot")
        except Exception as e:
            logging.error(e)
    return


async def get_size(size):
    """Get size in readable format"""
    units = ["Bytes", "KB", "MB", "GB", "TB", "PB", "EB"]
    size = float(size)
    i = 0
    while size >= 1024.0 and i < len(units):
        i += 1
        size /= 1024.0
    return "%.2f %s" % (size, units[i])


async def update_stats(m: Message, method):
    reply_markup = json.loads(str(m.reply_markup)) if m.reply_markup else ""
    message = m.caption.html if m.caption else m.text.html

    mdisk_links = re.findall(
        r'https?://mdisk.me[^\s`!()\[\]{};:".,<>?«»“”‘’]+', message +
        str(reply_markup)
    )
    droplink_links = await extract_link(message + str(reply_markup))
    total_links = len(droplink_links)

    await db.update_posts(1)

    if method == "mdisk":
        droplink_links = []
    if method == "shortener":
        mdisk_links = []

    await db.update_links(total_links, len(droplink_links), len(mdisk_links))


#  Heroku Stats
async def getRandomUserAgent():
    agents = [
        "Mozilla/5.0 (Windows NT 6.0; WOW64) AppleWebKit/534.24 (KHTML, like Gecko) Chrome/11.0.699.0 Safari/534.24",
        "Mozilla/5.0 (Windows NT 6.0; WOW64) AppleWebKit/535.1 (KHTML, like Gecko) Chrome/13.0.782.220 Safari/535.1",
        "Mozilla/5.0 (Windows NT 6.0; WOW64) AppleWebKit/535.1 (KHTML, like Gecko) Chrome/13.0.782.41 Safari/535.1",
        "Mozilla/5.0 (Windows NT 6.0; WOW64) AppleWebKit/535.11 (KHTML, like Gecko) Chrome/17.0.963.56 Safari/535.11",
        "Mozilla/5.0 (X11; CrOS i686 0.13.507) AppleWebKit/534.35 (KHTML, like Gecko) Chrome/13.0.763.0 Safari/534.35",
        "Mozilla/5.0 (X11; CrOS i686 0.13.587) AppleWebKit/535.1 (KHTML, like Gecko) Chrome/13.0.782.14 Safari/535.1",
        "Mozilla/5.0 (X11; CrOS i686 1193.158.0) AppleWebKit/535.7 (KHTML, like Gecko) Chrome/16.0.912.75 Safari/535.7",
        "Mozilla/5.0 (X11; CrOS i686 12.0.742.91) AppleWebKit/534.30 (KHTML, like Gecko) Chrome/12.0.742.93 Safari/534.30",
        "Mozilla/5.0 (X11; CrOS i686 12.433.109) AppleWebKit/534.30 (KHTML, like Gecko) Chrome/12.0.742.93 Safari/534.30",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/534.24 (KHTML, like Gecko) Chrome/11.0.696.34 Safari/534.24",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/534.24 (KHTML, like Gecko) Ubuntu/10.04 Chromium/11.0.696.0 Chrome/11.0.696.0 Safari/534.24",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/534.24 (KHTML, like Gecko) Ubuntu/10.10 Chromium/12.0.703.0 Chrome/12.0.703.0 Safari/534.24",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/535.21 (KHTML, like Gecko) Chrome/19.0.1042.0 Safari/535.21",
        "Opera/9.80 (Windows NT 5.1; U; sk) Presto/2.5.22 Version/10.50",
        "Opera/9.80 (Windows NT 5.1; U; zh-sg) Presto/2.9.181 Version/12.00",
        "Opera/9.80 (Windows NT 5.1; U; zh-tw) Presto/2.8.131 Version/11.10",
        "Opera/9.80 (Windows NT 5.1; U;) Presto/2.7.62 Version/11.01",
        "Opera/9.80 (Windows NT 5.2; U; en) Presto/2.6.30 Version/10.63",
        "Opera/9.80 (Windows NT 5.2; U; ru) Presto/2.5.22 Version/10.51",
        "Opera/9.80 (Windows NT 5.2; U; ru) Presto/2.6.30 Version/10.61",
        "Opera/9.80 (Windows NT 5.2; U; ru) Presto/2.7.62 Version/11.01",
        "Opera/9.80 (X11; Linux x86_64; U; pl) Presto/2.7.62 Version/11.00",
        "Opera/9.80 (X11; Linux x86_64; U; Ubuntu/10.10 (maverick); pl) Presto/2.7.62 Version/11.01",
        "Opera/9.80 (X11; U; Linux i686; en-US; rv:1.9.2.3) Presto/2.2.15 Version/10.10",
        "Mozilla/5.0 (Linux; Android 10; SM-G975F) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/81.0.4044.117 Mobile Safari/537.36",
    ]
    return agents[random.randint(0, len(agents) - 1)]


async def TimeFormatter(milliseconds) -> str:
    milliseconds = int(milliseconds) * 1000
    seconds, milliseconds = divmod(int(milliseconds), 1000)
    minutes, seconds = divmod(seconds, 60)
    hours, minutes = divmod(minutes, 60)
    days, hours = divmod(hours, 24)
    tmp = (
        (f"{str(days)}d, " if days else "")
        + (f"{str(hours)}h, " if hours else "")
        + (f"{str(minutes)}m, " if minutes else "")
        + (f"{str(seconds)}s, " if seconds else "")
        + (f"{str(milliseconds)}ms, " if milliseconds else "")
    )

    return tmp[:-2]


async def getHerokuDetails(h_api_key, h_app_name):
    if (not h_api_key) or (not h_app_name):
        logger.info("if you want heroku dyno stats, read readme.")
        return None
    try:
        heroku_api = "https://api.heroku.com"
        Heroku = heroku3.from_key(h_api_key)
        app = Heroku.app(h_app_name)
        useragent = await getRandomUserAgent()
        user_id = Heroku.account().id
        headers = {
            "User-Agent": useragent,
            "Authorization": f"Bearer {h_api_key}",
            "Accept": "application/vnd.heroku+json; version=3.account-quotas",
        }
        path = f"/accounts/{user_id}/actions/get-quota"

        async with aiohttp.ClientSession() as session:
            result = await session.get(heroku_api + path, headers=headers)

        result = await result.json()

        abc = ""
        account_quota = result["account_quota"]
        quota_used = result["quota_used"]
        quota_remain = account_quota - quota_used

        abc += f"<b>- Dyno Used:</b> `{await TimeFormatter(quota_used)}`\n"
        abc += f"<b>- Free:</b> `{await TimeFormatter(quota_remain)}`\n"
        # App Quota
        AppQuotaUsed = 0
        OtherAppsUsage = 0
        for apps in result["apps"]:
            if str(apps.get("app_uuid")) == str(app.id):
                try:
                    AppQuotaUsed = apps.get("quota_used")
                except Exception as t:
                    logger.error("error when adding main dyno")
                    logger.error(t)
            else:
                try:
                    OtherAppsUsage += int(apps.get("quota_used"))
                except Exception as t:
                    logger.error("error when adding other dyno")
                    logger.error(t)
        logger.info(f"This App: {str(app.name)}")
        abc += f"<b>- This App:</b> `{await TimeFormatter(AppQuotaUsed)}`\n"
        abc += f"<b>- Other:</b> `{await TimeFormatter(OtherAppsUsage)}`"
        return abc
    except Exception as g:
        logger.error(g)
        return None


async def get_me_button(user):
    user_id = user["user_id"]

    try:
        user["is_pvt_link"]
    except KeyError:
        await update_user_info(user_id, {"pvt_link": None, "is_pvt_link": False})

    buttons = []
    try:
        buttons = [
            [
                InlineKeyboardButton("Header Text", callback_data="ident"),
                InlineKeyboardButton(
                    "🚫 Click To Disable"
                    if user["is_header_text"]
                    else "✅ Click To Enable",
                    callback_data=f'setgs#is_header_text#{not user["is_header_text"]}#{str(user_id)}',
                ),
            ],
            [
                InlineKeyboardButton("Footer Text", callback_data="ident"),
                InlineKeyboardButton(
                    "🚫 Click To Disable"
                    if user["is_footer_text"]
                    else "✅ Click To Enable",
                    callback_data=f'setgs#is_footer_text#{not user["is_footer_text"]}#{str(user_id)}',
                ),
            ],
            [
                InlineKeyboardButton("Username", callback_data="ident"),
                InlineKeyboardButton(
                    "🚫 Click To Disable"
                    if user["is_username"]
                    else "✅ Click To Enable",
                    callback_data=f'setgs#is_username#{not user["is_username"]}#{str(user_id)}',
                ),
            ],
            [
                InlineKeyboardButton("Banner Image", callback_data="ident"),
                InlineKeyboardButton(
                    "🚫 Click To Disable"
                    if user["is_banner_image"]
                    else "✅ Click To Enable",
                    callback_data=f'setgs#is_banner_image#{not user["is_banner_image"]}#{str(user_id)}',
                ),
            ],
            [
                InlineKeyboardButton("Bitly Link", callback_data="ident"),
                InlineKeyboardButton(
                    "🚫 Click To Disable"
                    if user["is_bitly_link"]
                    else "✅ Click To Enable",
                    callback_data=f'setgs#is_bitly_link#{not user["is_bitly_link"]}#{str(user_id)}',
                ),
            ],
            [
                InlineKeyboardButton("Channel Link", callback_data="ident"),
                InlineKeyboardButton(
                    "🚫 Click To Disable"
                    if user["is_pvt_link"]
                    else "✅ Click To Enable",
                    callback_data=f'setgs#is_pvt_link#{not user["is_pvt_link"]}#{str(user_id)}',
                ),
            ],
            [
                InlineKeyboardButton("Hastag", callback_data="ident"),
                InlineKeyboardButton(
                    "🚫 Click To Disable" if user["is_hashtag"] else "✅ Click To Enable",
                    callback_data=f'setgs#is_hashtag#{not user["is_hashtag"]}#{str(user_id)}',
                ),
            ],
            [
                InlineKeyboardButton("Font", callback_data="ident"),
                InlineKeyboardButton(
                    "🚫 Click To Disable" if user["is_font"] else "✅ Click To Enable",
                    callback_data=f'setgs#is_font#{not user["is_font"]}#{str(user_id)}',
                ),
            ],
            [
                InlineKeyboardButton("Watermark", callback_data="ident"),
                InlineKeyboardButton(
                    "🚫 Click To Disable"
                    if user["watermark"]["status"]
                    else "✅ Click To Enable",
                    callback_data=f'boolsettings#watermark.status#{not user["watermark"]["status"]}',
                ),
            ],
            [
                InlineKeyboardButton("Forward Posts", callback_data="ident"),
                InlineKeyboardButton(
                    "🚫 Click To Disable"
                    if user["forward_channels"]["status"]
                    else "✅ Click To Enable",
                    callback_data=f'boolsettings#forward_channels.status#{not user["forward_channels"]["status"]}',
                ),
            ],
        ]
    except Exception as e:
        print(e)
    return buttons


async def user_api_check(user):
    user_method = user["method"]
    text = ""
    if user_method in ["mdisk", "mdlink"] and not user["mdisk_api"]:
        text += "\n\nSend your Mdisk API to continue..."
    if user_method in ["shortener", "mdlink"] and not user["shortener_api"]:
        text += f"\n\nSend your Shortener API to continue...\nCurrent Website {user['base_site']}"

    return text or True


async def encode(string):
    string_bytes = string.encode("ascii")
    base64_bytes = base64.urlsafe_b64encode(string_bytes)
    return base64_bytes.decode("ascii").strip("=")


async def file_store_handler(message, user):
    # FIle store Bot
    try:
        post_message: Message = await message.copy(
            chat_id=temp.DB_CHANNEL.id, disable_notification=True
        )
    except FloodWait as e:
        await asyncio.sleep(e.value)
        post_message = await message.copy(
            chat_id=temp.DB_CHANNEL.id, disable_notification=True
        )
    except Exception as e:
        logging.error(e)
        await message.reply_text("Something went Wrong while storing file")
        return
    try:
        converted_id = post_message.id * abs(temp.DB_CHANNEL.id)
        string = f"get-{converted_id}"
        base64_string = await encode(string)
        link = f"https://telegram.me/{Config.FILE_STORE_BOT_USERNAME}?start={base64_string}"
        link = await replace_link(user, link)
        reply_markup = InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton(
                        "🔁 Share URL", url=f"https://telegram.me/share/url?url={link}"
                    )
                ]
            ]
        )
        await message.reply_text(
            f"<b>Here is your link</b>\n\n{link}",
            reply_markup=reply_markup,
            disable_web_page_preview=True,
        )
    except Exception as e:
        logging.error(e, exc_info=True)


#  Tg DIRECT Link Generator
async def direct_gen_handler(c: Client, m: Message, user, mode: str):
    # FIle store Bot
    try:
        log_msg = await m.forward(chat_id=Config.DIRECT_GEN_DB)
        reply_markup, Stream_Text, stream_link = await gen_link(
            m=m, log_msg=log_msg, user=user, mode=mode
        )
        await log_msg.reply_text(
            text=f"**Requested By :** [{m.chat.first_name}](tg://user?id={m.chat.id})\n**Group ID :** `{m.from_user.id}`\n**Download Link :** {stream_link}",
            disable_web_page_preview=True,
            quote=True,
        )

        await m.reply_text(
            text=Stream_Text,
            disable_web_page_preview=True,
            reply_markup=reply_markup,
            quote=True,
        )
    except FloodWait as e:
        print(f"Sleeping for {str(e.value)}s")
        await asyncio.sleep(e.value)
        await c.send_message(
            chat_id=Config.DIRECT_GEN_DB,
            text=f"Got Floodwait Of {str(e.x)}s from [{m.from_user.first_name}](tg://user?id={m.from_user.id})\n\n**User ID :** `{str(m.from_user.id)}`",
            disable_web_page_preview=True,
        )


def get_media_from_message(message: "Message"):
    media_types = (
        "audio",
        "document",
        "photo",
        "sticker",
        "animation",
        "video",
        "voice",
        "video_note",
    )
    for attr in media_types:
        if media := getattr(message, attr, None):
            return media


def get_hash(media_msg: Message) -> str:
    media = get_media_from_message(media_msg)
    return getattr(media, "file_unique_id", "")[:6]


def get_media_file_size(m):
    media = get_media_from_message(m)
    return getattr(media, "file_size", "None")


def get_name(media_msg: Message) -> str:
    media = get_media_from_message(media_msg)
    return getattr(media, "file_name", "None")


def get_media_mime_type(m):
    media = get_media_from_message(m)
    return getattr(media, "mime_type", "None/unknown")


def get_media_file_unique_id(m):
    media = get_media_from_message(m)
    return getattr(media, "file_unique_id", "")


def humanbytes(size):
    # https://stackoverflow.com/a/49361727/4723940
    # 2**10 = 1024
    if not size:
        return ""
    power = 2**10
    n = 0
    Dic_powerN = {0: " ", 1: "Ki", 2: "Mi", 3: "Gi", 4: "Ti"}
    while size > power:
        size /= power
        n += 1
    return f"{str(round(size, 2))} {Dic_powerN[n]}B"


# Generate Text, Stream Link, reply_markup
async def gen_link(m: Message, log_msg: Messages, user, mode):
    """Generate Text for Stream Link, Reply Text and reply_markup"""
    # lang = getattr(Language, message.from_user.language_code)

    file_name = get_name(log_msg)
    file_size = humanbytes(get_media_file_size(log_msg))

    page_link = (
        org_page_link
    ) = f"{Config.DIRECT_GEN_URL}watch/{get_hash(log_msg)}{log_msg.id}"
    stream_link = (
        stream_org_link
    ) = f"{Config.DIRECT_GEN_URL}{log_msg.id}/{quote_plus(get_name(m))}?hash={get_hash(log_msg)}"

    # short
    page_link = await replace_link(user, page_link)
    stream_link = await replace_link(user, stream_link)

    if mode == "direct":
        txt = f"<b>🔗Original Download Link :</b> **[Cʟɪᴄᴋ Hᴇʀᴇ]({stream_org_link})**\n\n<b>📥 Shorted Download link :</b> `{stream_link}`\n\n"

        Stream_Text = Config.stream_msg_text.format(file_name, file_size) + txt
    elif mode == "stream":
        txt = f"<b>🔗Original Stream Link :</b> **[Cʟɪᴄᴋ Hᴇʀᴇ]({org_page_link})**\n\n<b>🖥 Shorted Watch link :</b> `{page_link}`"

        Stream_Text = Config.stream_msg_text.format(file_name, file_size) + txt

    btn = (
        [InlineKeyboardButton("Shorted Stream link 🖥", url=page_link)]
        if mode == "stream"
        else [InlineKeyboardButton(" Shorted Dᴏᴡɴʟᴏᴀᴅ Link 📥", url=stream_link)]
    )
    reply_markup = InlineKeyboardMarkup(
        [
            btn,
        ]
    )

    return reply_markup, Stream_Text, stream_link


async def _update_existing_users():
    filters = {"watermark": {"$exists": False}, "channels": {"$exists": False}}
    update = {
        "$set": {
            "watermark": {
                "watermark_color": "white",
                "status": True,
                "watermark_text": None,
                "watermark_position": ("center", "center"),
                "watermark_size": 50,
                "watermark_font": "Helvetica-Bold",
                "watermark_opacity": 1.0,
            },
            "forward_channels": {"status": False, "channels": []},
        }
    }
    await update_existing_users(filters, update)


async def _update_existing_vars():
    update = {"join_channel_username": None}
    await db.update_bot_vars(update)


async def get_response(url):
    client = requests.Session()
    res = client.get(url)
    return res.json()


def is_enabled(value):
    if value.lower() in ["true", "yes", "1", "enable", "y"]:
        return True
    elif value.lower() in ["false", "no", "0", "disable", "n"]:
        return False


async def make_vars():
    bot_vars = await db.get_bot_vars()
    Config.ADMINS = bot_vars["admins"]
    Config.BROADCAST_AS_COPY = bot_vars["broadcast_as_copy"]
    Config.IS_PRIVATE = bot_vars["is_private"]
    Config.CHANNELS = bot_vars["channels"]
    Config.CHANNEL_ID = bot_vars["channel_id"]
    Config.USERNAME = bot_vars["username"]
    Config.HASHTAG = bot_vars["hashtag"]
    Config.HEADER_TEXT = bot_vars["header_text"]
    Config.FOOTER_TEXT = bot_vars["footer_text"]
    Config.BANNER_IMAGE = bot_vars["banner_image"]
    Config.WELCOME_IMAGE = bot_vars["welcome_image"]
    Config.LINK_BYPASS = bot_vars["link_bypass"]
    Config.VERIFIED_TIME = bot_vars["verified_time"]
    Config.LOG_CHANNEL = bot_vars["log_channel"]
    Config.UPDATE_CHANNEL = bot_vars["update_channel"]
    Config.KEYBOARD_BUTTON = bot_vars["keyboard_button"]

    Config.IS_MDISK = bot_vars["is_mdisk"]
    Config.IS_DEFAULT_BASE_SITE = bot_vars["is_default_base_site"]
    Config.FILE_STORE_DB = bot_vars["file_store_db"]
    Config.FILE_STORE_BOT_USERNAME = bot_vars["file_store_bot_username"]
    Config.FILE_STORE = bool(
        Config.FILE_STORE_DB and Config.FILE_STORE_BOT_USERNAME)

    Config.DIRECT_GEN_DB = bot_vars["direct_gen_db"]
    Config.DIRECT_GEN_BOT_USERNAME = bot_vars["direct_gen_bot_username"]
    Config.DIRECT_GEN_URL = bot_vars["direct_gen_url"]
    Config.DIRECT_GEN = bool(
        Config.DIRECT_GEN_DB
        and Config.DIRECT_GEN_BOT_USERNAME
        and Config.DIRECT_GEN_URL
    )

    Config.IS_BINDASSLINKS = bot_vars["is_bindasslinks"]
    Config.IS_DROPLINK = bot_vars["is_droplink"]
    Config.IS_TNLINKS = bot_vars["is_tnlinks"]
    Config.IS_INDIANSHORTENER = bot_vars["is_indianshortener"]
    Config.IS_EASYSKY = bot_vars["is_easysky"]
    Config.IS_LINKSHORTIFY = bot_vars["is_linkshortify"]
    Config.IS_EARNL_SITE = bot_vars["is_earnl_site"]
    Config.IS_EARNL_XYZ = bot_vars["is_earnl_xyz"]

    Config.START_MESSAGE = bot_vars["start_message"]
    Config.HELP_MESSAGE = bot_vars["help_message"]
    Config.ABOUT_TEXT = bot_vars["about_message"]
    Config.METHOD_MESSAGE = bot_vars["method_message"]
    Config.USER_ABOUT_MESSAGE = bot_vars["user_about_message"]
    Config.MDISK_API_MESSAGE = bot_vars["mdisk_api_message"]
    Config.SHORTENER_API_MESSAGE = bot_vars["shortener_api_message"]
    Config.USERNAME_TEXT = bot_vars["username_message"]
    Config.HASHTAG_TEXT = bot_vars["hashtag_message"]
    Config.PVT_LINKS_TEXT = bot_vars["pvt_links_message"]
    Config.BANNER_IMAGE_TEXT = bot_vars["banner_image_message"]
    Config.INCLUDE_DOMAIN_TEXT = bot_vars["include_domain_message"]
    Config.EXCLUDE_DOMAIN_TEXT = bot_vars["exclude_domain_message"]
    Config.BITLY_API_MESSAGE = bot_vars["bitly_api_message"]
    Config.FEATURES_MESSAGE = bot_vars["features_message"]
    Config.BALANCE_CMD_TEXT = bot_vars["balance_message"]
    Config.ACCOUNT_CMD_TEXT = bot_vars["account_message"]
    Config.HEADER_MESSAGE = bot_vars["header_message"]
    Config.SHORTENER_API_MESSAGE = bot_vars["shortener_api_message"]
    Config.FOOTER_MESSAGE = bot_vars["footer_message"]
    Config.USERNAME = bot_vars["join_channel_username"]


def is_float(value):
    try:
        float(value)
        return True
    except ValueError:
        return False


async def get_font_list():
    return [
        font.replace(".ttf", "").replace(".otf", "")
        for font in os.listdir("fonts")
        if (font.endswith(".ttf") or font.endswith(".otf")) and not font.startswith("._")
    ]


async def get_font_image(font_name, text, font_size=50, font_style=None):
    font_file = await search_file(Config.FONT_DIR, f"{font_name}")
    if font_file is None:
        return None
    # create a new image with a white background
    image = Image.new('RGBA', (500, 200), (255, 255, 255, 255))
    # create a drawing context
    draw = ImageDraw.Draw(image)
    # specify the font and text to draw
    font = ImageFont.truetype(font_file, font_size)
    # get the size of the text in the specified font
    text_width, text_height = draw.textsize(text, font=font)
    # calculate the center coordinates of the image
    x = (image.width - text_width) / 2
    y = (image.height - text_height) / 2
    # draw the text in the specified font and style at the center coordinates
    draw.text((x, y), text, font=font, fill=(0, 0, 0, 255))
    # save the image to a file
    file_name = f"downloads/{font_name.replace(' ', '_')}.png"
    image.save(file_name)
    return file_name


async def search_file(directory, pattern):
    """Searches for a file matching the specified pattern in the specified directory,
    excluding the file extension while searching, and including the extension while
    returning the result value.

    Args:
        directory (str): The directory to search in.
        pattern (str): The pattern to search for, without the file extension.

    Returns:
        The file path matching the specified pattern, including the file extension,
        or None if no match was found.
    """
    for root, dirnames, filenames in os.walk(directory):
        for filename in fnmatch.filter(filenames, f'{pattern}.*'):
            return os.path.join(root, filename)
    return Config.DEFAULT_FONT_FILE


async def apply_watermark(
    image_path,
    watermark_text,
    font_path,
    watermark_fontsize,
    watermark_color,
    watermark_opacity,
    watermark_position,
):
    # Open the image
    image = Image.open(image_path).convert("RGBA")

    # Create a blank image for the watermark, with transparency
    watermark = Image.new("RGBA", image.size, (255, 255, 255, 0))

    # Get a drawing context for the watermark image
    draw = ImageDraw.Draw(watermark)

    # Load the font
    print(font_path)
    font = ImageFont.truetype(font_path, watermark_fontsize)

    watermark_color = webcolors.name_to_rgb(watermark_color)
    # Draw the text onto the watermark image
    # Draw the text onto the watermark image
    text_bbox = draw.textbbox((0, 0), watermark_text, font=font)
    text_width = text_bbox[2] - text_bbox[0]
    text_height = text_bbox[3] - text_bbox[1]
    # Calculate the x, y coordinates of the text
    margin = 50

    watermark_position = (watermark_position[1], watermark_position[0])

    if watermark_position[0] == "left":
        text_x = margin
    elif watermark_position[0] == "right":
        text_x = image.size[0] - text_width - margin
    else:
        text_x = (image.size[0] - text_width) / 2

    if watermark_position[1] == "top":
        text_y = margin
    elif watermark_position[1] == "bottom":
        text_y = image.size[1] - text_height - margin
    else:
        text_y = (image.size[1] - text_height) / 2

    draw.text(
        (text_x, text_y),
        watermark_text,
        font=font,
        fill=watermark_color + (int(255 * watermark_opacity),),
    )

    # Combine the image and watermark using alpha blending
    result = Image.alpha_composite(image, watermark)

    return result


async def download_image(url: str, folder: str) -> str:
    # Make the folder if it doesn't exist
    if not os.path.exists(folder):
        os.makedirs(folder)

    # Download the image from the URL
    response = requests.get(url)

    # Get the filename from the URL
    filename = os.path.basename(url)

    # Save the image to a file in the folder
    filepath = os.path.join(folder, filename)
    with open(filepath, 'wb') as f:
        f.write(response.content)

    return filepath
