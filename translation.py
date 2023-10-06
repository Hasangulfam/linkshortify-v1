from pyrogram.types import (
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    KeyboardButton,
    ReplyKeyboardMarkup,
    ReplyKeyboardRemove,
)
from config import Config


Config.BATCH_MESSAGE = BATCH = """
This command is used to short or convert links from first to last posts

Make the bot as an admin in your channel

Command usage: `/batch [channel id or username]`

Ex: `/batch -100xxx`
"""

Config.START_MESSAGE = """🄷🄴🄻🄻🄾, {}
**I'm gyanilinks.com  Official Bot I Can Convert  Bulk Links To Yours Short Links From Direct Your gyanilinks.com Account With Just a Simple Clicks😍\n\n** 
**How To Use 🤔\n ✅1. Got To [https://bit.ly/3cbbgs0](https://bindaaslinks.com/ref/bhatmanjusms) & Complete Your Registration.\n ✅2.Get Your API https://gyanilinks.com/member/tools/api Copy Your API \n ✅3. Add your api using command /api \n Example : `/Api 0beb1135aac920c1e89856847ef4e8e03e8547a9` \n\n**
** For More Help Press /Help**

**ᴄᴜʀʀᴇɴᴛ ᴍᴇᴛʜᴏᴅ sᴇʟᴇᴄᴛᴇᴅ: {}**
**made with: {}**
"""


Config.HELP_MESSAGE = """**
Hey! My name is {firstname}. I am a Link Convertor and Shortener Bot, here to make your Work Easy and Help you to Earn more

👇 USEFULL COMMANDS 👇

〽️ Hit 👉 /start To Know More About How To Link bindaaslinks.com Account To This Bot.

🤘 Hit 👉 /features To Know More Features Of This Bot.

📝 Hit 👉 /watermark To Know More About Adding Your Custom Watermark In Your Post

💁‍♀️ Hit 👉 /help To Get Help.

🔗 Hit 👉 /Api To Link Your Bindaaslinks Account 

Ⓜ️ Hit 👉 /mdisk_api Link Your Mdisk Account To Converter Others Mdisk Links To Your Mdisklink + Bindaaslinks

🅱 Hit 👉 /bitly_api Link Your Bitly account To Converter Links To Bitly 

⬇️ Hit 👉 /footer To Get Help About Adding your Custom Footer In Your Post

⬆️ Hit 👉 /header To Get Help About Adding Your Custom Header In Your Post

🖼️ Hit 👉 /banner_image To Add Banner In Photo

🔁 Hit 👉 /username To Change Others Username To Your Username

⚙ Hit 👉 /settings To Set settings As per your wish

IF You need More HeLp Then Contact @BindaasLinksIndia ♥️**"""


Config.ABOUT_TEXT = """**👉Know More: 

➲🤖 ʙᴏᴛ ɴᴀᴍᴇ  :  {} 

➲✅ sɪᴛᴇ ɴᴀᴍᴇ : Earnl.site

➲📢 ᴏғғɪᴄɪᴀʟ ᴄʜᴀɴɴᴇʟ : [ᴄʟɪᴄᴋ ʜᴇʀᴇ](https://telegram.me/gyanilinks)

➲🤑 ᴄᴜʀʀᴇɴᴛ ᴄᴘᴍ : [ᴄʟɪᴄᴋ ʜᴇʀᴇ](https://gyanilinks.com/payout-rates)

➲☎️ ᴄᴏɴᴛᴀᴄᴛ sᴜᴘᴘᴏʀᴛ : [ᴄʟɪᴄᴋ ʜᴇʀᴇ](https://t.me/idblant)

➲👨‍💻 ʙᴏᴛ ᴅᴇᴠᴇʟᴏᴘᴇʀ : [ᴄʟɪᴄᴋ ʜᴇʀᴇ](http://t.me/CR_0O0)

sᴏ ɴᴏᴡ sᴇɴᴅ ᴍᴇ ᴛʜᴇ ʟɪɴᴋs, ɪ ᴡɪʟʟ ᴄᴏɴᴠᴇʀᴛ ɪᴛ ᴀɴᴅ ɢɪᴠᴇ ɪᴛ ᴛᴏ ʏᴏᴜ 😊  ɪғ ʏᴏᴜ ɴᴇᴇᴅ sᴀᴍᴇ ʙᴏᴛ ᴛᴏ ʏᴏᴜ'ʀᴇ sʜᴏʀᴛɴᴇʀ ᴛʜᴇɴ ᴄᴏɴᴛᴀᴄᴛ @CR_0O0
**"""

is_mdisk = "\n> `mdisk` - Save all the links of the post to your Mdisk account.\n"

Config.METHOD_MESSAGE = (
    """
Current Method: {method}
                
Methods Available:

> `Mdiak+shortner` - Change all the links of the post to your MDisk account first and then short to {shortener} link.

> `shortener` - Short all the links of the post to link directly.
%s
To change method, choose it from the following options:
            """
    % is_mdisk
    if Config.IS_MDISK
    else ""
)


Config.CUSTOM_ALIAS_MESSAGE = """For custom alias, `[link] | [custom_alias]`, Send in this format

This feature works only in private mode only

Ex: https://t.me/example | Example"""


Config.ADMINS_MESSAGE = """
List of Admins who has access to this Bot

{admin_list}
"""


Config.CHANNELS_LIST_MESSAGE = """
List of channels that have access to this Bot:

{channels}"""


HELP_REPLY_MARKUP = InlineKeyboardMarkup(
    [
        [
            InlineKeyboardButton("Batch", callback_data="cbatch_command"),
        ],
        [
            InlineKeyboardButton("Custom Alias", callback_data="alias_conf"),
            InlineKeyboardButton("Admins", callback_data="admins_list"),
        ],
        [
            InlineKeyboardButton("Channels", callback_data="channels_list"),
            InlineKeyboardButton("Watermark", callback_data="watermark_settings"),
        ],
        [
            InlineKeyboardButton("Home", callback_data="start_command"),
        ],
    ]
)


ABOUT_REPLY_MARKUP = InlineKeyboardMarkup(
    [
        [
            InlineKeyboardButton("Home", callback_data="start_command"),
            InlineKeyboardButton("Help", callback_data="help_command"),
        ],
        [InlineKeyboardButton("Close", callback_data="delete")],
    ]
)

START_MESSAGE_REPLY_MARKUP = InlineKeyboardMarkup(
    [
        [
            InlineKeyboardButton("Help", callback_data="help_command"),
            InlineKeyboardButton("About", callback_data="about_command"),
        ],
        [
            InlineKeyboardButton("Method", callback_data="method_command"),
            InlineKeyboardButton(
                "Join Channel♥️", url=f"https://telegram.me/{Config.USERNAME}"
            ),
        ],
        [InlineKeyboardButton("Close", callback_data="delete")],
    ]
)

START_MESSAGE_KEYBOARD = ReplyKeyboardMarkup(
    [
        [KeyboardButton(text="▶️ 𝙎𝙩𝙖𝙧𝙩")],
        [
            KeyboardButton(text="🆘 𝙃𝙚𝙡𝙥"),
            KeyboardButton(text="📝 𝘼𝙗𝙤𝙪𝙩"),
            KeyboardButton(text="💡 𝙁𝙚𝙖𝙩𝙪𝙧𝙚𝙨"),
        ],
        [
            KeyboardButton(text="🔗 𝘼𝙋𝙄"),
            KeyboardButton(text="🅱 𝘽𝙞𝙩𝙡𝙮 𝘼𝙋𝙄"),
        ],
        [
            KeyboardButton(text="⚙️ 𝙎𝙚𝙩𝙩𝙞𝙣𝙜𝙨"),
            KeyboardButton(text="🪪 𝘼𝙘𝙘𝙤𝙪𝙣𝙩"),
        ],
        [KeyboardButton(text="🅰 𝙁𝙤𝙣𝙩𝙨"), KeyboardButton(text="💰 𝘽𝙖𝙡𝙖𝙣𝙘𝙚")],
        [KeyboardButton(text="⬆️ 𝙃𝙚𝙖𝙙𝙚𝙧"), KeyboardButton(text="⬇️ 𝙁𝙤𝙤𝙩𝙚𝙧")],
        [KeyboardButton(text="🏷 𝙐𝙨𝙚𝙧𝙣𝙖𝙢𝙚"), KeyboardButton(text="🔖 𝙃𝙖𝙨𝙝𝙩𝙖𝙜")],
        [KeyboardButton(text="⛓ 𝘾𝙝𝙖𝙣𝙣𝙚𝙡 𝙇𝙞𝙣𝙠"), KeyboardButton(text="🏞 𝘽𝙖𝙣𝙣𝙚𝙧 𝙄𝙢𝙖𝙜𝙚")],
        [
            KeyboardButton(text="🗃 𝙁𝙞𝙡𝙚 𝙎𝙩𝙤𝙧𝙚 𝙇𝙞𝙣𝙠"),
            KeyboardButton(text="📡 𝙎𝙩𝙧𝙚𝙖𝙢 𝙇𝙞𝙣𝙠"),
        ],
        [
            KeyboardButton(text="📥 𝘿𝙞𝙧𝙚𝙘𝙩 𝘿𝙤𝙬𝙣𝙡𝙤𝙖𝙙 𝙇𝙞𝙣𝙠"),
            KeyboardButton(text="🔄 𝘽𝙮𝙥𝙖𝙨𝙨"),
        ],
        [
            KeyboardButton(text="🎨 𝙒𝙖𝙩𝙚𝙧𝙢𝙖𝙧𝙠"),
            KeyboardButton(text="⏩️ 𝙁𝙤𝙧𝙬𝙖𝙧𝙙 𝘾𝙝𝙖𝙣𝙣𝙚𝙡𝙨"),
        ],
        [KeyboardButton(text="❌ 𝘾𝙡𝙤𝙨𝙚 𝘽𝙪𝙩𝙩𝙤𝙣𝙨")],
    ],
    one_time_keyboard=1,
    resize_keyboard=1,
)


BACK_REPLY_MARKUP = InlineKeyboardMarkup(
    [[InlineKeyboardButton("Back", callback_data="help_command")]]
)


BASE_SITE_REPLY_MARKUP = InlineKeyboardMarkup(
    [
        [InlineKeyboardButton(site, callback_data=f"change_site#{site}")]
        for site in Config.base_sites
    ]
)

FONT_REPLY_MARKUP = InlineKeyboardMarkup(
    [
        [InlineKeyboardButton(font.title(), callback_data=f"change_font#{font}")]
        for font in Config.font_dict.keys()
    ]
)

Config.USER_ABOUT_MESSAGE = """**
- sʜᴏʀᴛᴇɴᴇʀ ᴡᴇʙsɪᴛᴇ: {base_site}

- ᴍᴇᴛʜᴏᴅ: {method}

- {base_site} ᴀᴘɪ: {shortener_api}

- ᴍᴅɪsᴋ ᴀᴘɪ: {mdisk_api}

- ʙɪᴛʟʏ ᴀᴘɪ: {bitly_api}

- ᴜsᴇʀɴᴀᴍᴇ: @{username}

- Channel link: {channel_link}

- ʜᴇᴀᴅᴇʀ ᴛᴇxᴛ: 
{header_text}

- ғᴏᴏᴛᴇʀ ᴛᴇxᴛ: 
{footer_text}

- ʙᴀɴɴᴇʀ ɪᴍᴀɢᴇ: {banner_image}

- Hashtag: {hashtag}
**"""


Config.MDISK_API_MESSAGE = """**To add or update your Mdisk API, \n`/mdisk_api mdisk_api`
            
Ex: `/mdisk_api 6LZq851sXoPHugiKQq`
            
Others Mdisk Links will be automatically changed to the API of this Mdisk account

Current Mdisk API: `{}`**"""


Config.SHORTENER_API_MESSAGE = """**To add or update your Shortner Website API, 
`/shortener_api [api]`
            
Ex: `/api 6LZq851sXofffPHugiKQq`

Current Website: {base_site}

Current Shortener API: `{shortener_api}`**"""


Config.HEADER_MESSAGE = """**Reply to the Header Text You Want

This Text will be added to the top of every message caption or text

Example :- `/Header Join @filmyfunda_movies` 

To Remove Header Text: `/header remove`**"""


Config.FOOTER_MESSAGE = """**Reply to the Footer Text You Want

This Text will be added to the bottom of every message caption or text


Example :- `/Footer Join @filmyfunda_movies` 

To Remove Footer Text: `/footer remove`**"""


Config.USERNAME_TEXT = """"**Current Username: {username}

Usage: `/username your_username`

This username will be automatically replaced with other usernames in the post


Example :- `/username @CR_0O0` 

To remove this username, `/username remove`**"""


Config.HASHTAG_TEXT = """**Current Hashtag: {hashtag}

Usage: `/hashtag your_hashtag`

This hashtag will be automatically replaced with other hashtags in the post

Example :- `/hashtag instagramdown` 

To remove this hashtag, `/hashtag remove`**"""


Config.PVT_LINKS_TEXT = """**Current Channel Links: {pvt_link}

Usage: `/channel_link https://t.me/+riua0Y3YXHo4NjY1`

This Channel Link will be automatically replaced with other private links in the post

Example :- `/channel_link https://t.me/+riua0Y3YXHo4NjY1` 

To remove this Channel Link, `/channel_link remove`**"""


Config.BANNER_IMAGE_TEXT = """**Current Banner Image URL: {banner_image}

Usage: `firat send your image after reply that image with /banner_image command`

This image will be automatically replaced with other images in the post

To remove custom image, `/banner_image remove`

Eg: `/banner_image https://www.nicepng.com/png/detail/436-4369539_movie-logo-film.png`**"""


Config.INCLUDE_DOMAIN_TEXT = """**
Use this option if you want to short only links from the following domains list.

Current Include Domain:
{}

Usage: /include_domain domain_name
Ex: /include_domain t.me

To remove a domain, `/include_domain remove domain_name
Ex: /include_domain remove t.me

To remove all domains, `/include_domain remove_all
Ex: /include_domain remove_all
**"""


Config.EXCLUDE_DOMAIN_TEXT = """**
Use this option if you wish to short every link on your channel but exclude only the links from the following domains list

Current Exclude Domains:
{}

Usage: /exclude_domain domain_name
Ex: /exclude_domain t.me

To remove a domain, `/exclude_domain remove domain_name
Ex: /exclude_domain remove t.me

To remove all domains, `/exclude_domain remove_all
Ex: /exclude_domain remove_all
**"""


Config.BITLY_API_MESSAGE = """**To add or update your Bitly API , 
`/bitly_api [api]`
            
Ex: `/bitly_api 6LZq851sXofffPHugiKQq`

Current API: `{bitly_api}`**"""

Config.FEATURES_MESSAGE = "**Hello, {first_name}!**\n\n**💠 Features Of Link Shortner Bot 💠\n\n❤️ It's A User Friendly Bot ❤️\n\n➡️ Use Can Short Bulk Links Into Your Shortner Account With This Bot\n\n➡️ You Can Also Short Links With Custom Alias\n\n➡️ You Can Also Use Mdisk Links To Short It Into Your Mdisk Account And Then Shortner Account\n\n➡️ You Can Set Custom Header\n\n➡️ You Can Set Custom Footer\n\n➡️ You Can Set Custom Banner Image\n\n➡️ You Can Chage Telegram Username\n\n➡️ You Can replace others channel links to your channel link\n\n➡️ You Can Use Bitly To Short shortner Link\n\n➡️ You Can Chose Different Link Short Methods\n\n➡️ You Can Use Settings Section To Manage All Things At One Place\n\n➡️ You Can Send File To Bot And Bot Will Give You Different shortner Links & It Will Be Usable To Download File Directly, Streaming It Online & Download File From File To Link Bot\n\n➡️ You Can Change Other Shortner Links To Your Shortner Account Links\n\n➡️ Bot can also short hidden links and hyperlinks\n\n➡️ Bot can short button links also\n\n⚠️ if you need same bot to your shortner site then contact me @CR_0O0 ⚡️**"


Config.BALANCE_CMD_TEXT = """
🔰 Account Username : {username} 

➡️ Publisher Earnings : {publisher_earnings}
➡️ Referral Earning : {referral_earnings}

✅ Available Balance : {available_balance}

👇🏻Click Hear To Withdraw Your Earnings 👇🏻"""


Config.ACCOUNT_CMD_TEXT = """
🔰 Username : {username} 
📧 Email Address : {email} 

💠 Withdrawal Method : {withdrawal_method} 
➡️ Withdrawal Account : {withdrawal_account}

🔗 Referral Link : {referral_link}

👇 Click Here To Share Your Referral Link 👇"""

Config.ADD_ADMIN_TEXT = """Current Admins:
{}
Usage: /addadmin id
Ex: `/addadmin 14035272, 14035272`
To remove a admin,
Ex: `/addadmin remove 14035272`
To remove all admins,
Ex: `/addadmin remove_all`
"""
