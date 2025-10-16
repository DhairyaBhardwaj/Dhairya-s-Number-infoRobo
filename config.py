

import os
from os import environ,getenv
import logging
from logging.handlers import RotatingFileHandler

#nothin on Tg
#--------------------------------------------
#Bot token @Botfather
BOT_USERNAME = os.environ.get("BOT_USERNAME", "Number_toinfo_bot")
TG_BOT_TOKEN = os.environ.get("TG_BOT_TOKEN", "8496102678:AAG3BJ7IN1vw2E-HWnfmP-qWS4p2Do05ya4")
APP_ID = int(os.environ.get("APP_ID", "29463066")) #Your API ID from my.telegram.org
API_HASH = os.environ.get("API_HASH", "b2f2a28941783eaadacca2f917ffec0a") #Your API Hash from my.telegram.org
#--------------------------------------------

DISABLE_CHANNEL_BUTTON = os.environ.get("DISABLE_CHANNEL_BUTTON", False)
CHANNEL_ID = int(os.environ.get("CHANNEL_ID", "-1003150849494")) #Your db channel Id
OWNER = os.environ.get("OWNER", "Dhairya_bh") # Owner username without @
OWNER_ID = int(os.environ.get("OWNER_ID", "5968801459")) # Owner id
ADMINS = [6937607934, 6937607935, 5848573966]
#--------------------------------------------
PORT = os.environ.get("PORT", "8080")
#--------------------------------------------
DB_URI = os.environ.get("DATABASE_URL", "mongodb+srv://x4ngo03:zWQmajZZPpLfaJs4@cluster0.g3eapwn.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0")
DB_NAME = os.environ.get("DATABASE_NAME", "des1br")
#--------------------------------------------
FSUB_LINK_EXPIRY = int(os.getenv("FSUB_LINK_EXPIRY", "0"))  # 0 means no expiry
BAN_SUPPORT = os.environ.get("BAN_SUPPORT", "https://t.me/sayxsee_support")
TG_BOT_WORKERS = int(os.environ.get("TG_BOT_WORKERS", "200"))
#--------------------------------------------
START_PIC = os.environ.get("START_PIC", "https://i.imghippo.com/files/JDB7578JRA.jpg")
FORCE_PIC = os.environ.get("FORCE_PIC", "https://i.imghippo.com/files/ltNH2419OV.jpg")
#--------------------------------------------

#--------------------------------------------

# --- HELP MESSAGE ---
HELP_TXT = "<b><blockquote>ᴛʜɪs ɪs ᴛʜᴇ ᴏғғɪᴄɪᴀʟ ʜᴇʟᴘ ᴅᴏᴄᴜᴍᴇɴᴛ ғᴏʀ ᴛʜᴇ ɪɴᴅɪᴀɴ ᴏsɪɴᴛ ʟᴏᴏᴋᴜᴘ ʙᴏᴛ, ᴘᴏᴡᴇʀᴇᴅ ʙʏ <a href='http://sayxsee.xyz'>sᴀʏx𝐬ᴇᴇ.xʏᴢ</a>.\n\n❏ ʙᴏᴛ ᴄᴏᴍᴍᴀɴᴅs\n├/start : ʀᴇsᴛᴀʀᴛs ᴛʜᴇ ʙᴏᴛ ᴀɴᴅ ᴄʜᴇᴄᴋs ғsᴜʙ\n├/myplan : ᴄʜᴇᴄᴋ ʏᴏᴜʀ ᴘʀᴇᴍɪᴜᴍ sᴛᴀᴛᴜs\n├/credits : sʜᴏᴡs ʏᴏᴜʀ ʀᴇᴍᴀɪɴɪɴɢ ғʀᴇᴇ ᴛʀɪᴇs\n├/referral : ɢᴇᴛ ʏᴏᴜʀ ʀᴇғᴇʀʀᴀʟ ʟɪɴᴋ\n├/about : ɢᴇᴛ ᴅᴇᴠᴇʟᴏᴘᴇʀ ᴀɴᴅ sᴜᴘᴘᴏʀᴛ ɪɴғᴏ\n└/help : ʏᴏᴜ ᴀʀᴇ ʜᴇʀᴇ\n\nsɪᴍᴘʟʏ sᴇɴᴅ ᴀɴ ɪɴᴅɪᴀɴ ɴᴜᴍʙᴇʀ (ᴇ.ɢ., +91...) ᴛᴏ ʙᴇɢɪɴ ʏᴏᴜʀ sᴇᴀʀᴄʜ.\n\nғᴏʀ sᴜᴘᴘᴏʀᴛ: ᴄᴏɴᴛᴀᴄᴛ ᴏᴜʀ sᴜᴘᴘᴏʀᴛ ʙᴏᴛ <a href='https://t.me/Connect_SayXSee_Bot'>@Connect_SayXSee_Bot</a></blockquote></b>"

# --- ABOUT MESSAGE (U+200B cleaned) ---
ABOUT_TXT = "<b><blockquote>◈ ᴅᴇᴠᴇʟᴏᴘᴇᴅ & ᴍᴀɪɴᴛᴀɪɴᴇᴅ ʙʏ: <a href='http://sayxsee.xyz'>sᴀʏx𝐬ᴇᴇ.xʏᴢ</a>\n◈ ᴏғғɪᴄɪᴀʟ ᴛᴇʟᴇɢʀᴀᴍ ᴄʜᴀɴɴᴇʟ: <a href='https://t.me/+10TQd-BMf3I0MjM1'>sᴀʏx𝐬ᴇᴇ ᴄʜᴀɴɴᴇʟ</a>\n◈ ᴏғғɪᴄɪᴀʟ sᴜᴘᴘᴏʀᴛ ʙᴏᴛ: <a href='https://t.me/Connect_SayXSee_Bot'>@Connect_SayXSee_Bot</a>\n◈ sᴜᴘᴘᴏʀᴛ ᴘᴀɢᴇ: <a href='http://sayxsee.xyz/contact'>sᴀʏx𝐬ᴇᴇ.xʏᴢ/ᴄᴏɴᴛᴀᴄᴛ</a>\n\nᴛʜɪs ʙᴏᴛ ᴘʀᴏᴠɪᴅᴇs ᴏsɪɴᴛ ᴅᴀᴛᴀ ʟᴏᴏᴋᴜᴘs ʙᴀsᴇᴅ ᴏɴ ᴀᴄᴄᴇssᴇᴅ ᴅᴀᴛᴀsᴇᴛs.</blockquote></b>"
#--------------------------------------------
START_MSG = os.environ.get("START_MESSAGE", "<b>ʜᴇʟʟᴏ {mention}\n\n<blockquote> ɪ ᴀᴍ ᴛʜᴇ ɪɴᴅɪᴀɴ ᴏsɪɴᴛ ʟᴏᴏᴋᴜᴘ ʙᴏᴛ. ɪ ᴄᴀɴ sᴇᴀʀᴄʜ ᴅᴇᴛᴀɪʟs ʟɪᴋᴇ ғᴜʟʟ ɴᴀᴍᴇ, ғᴀᴛʜᴇʀ's ɴᴀᴍᴇ, ᴀɴᴅ ᴀᴅᴅʀᴇssᴇs ᴀɢᴀɪɴsᴛ ᴀɴ ɪɴᴅɪᴀɴ ᴘʜᴏɴᴇ ɴᴜᴍʙᴇʀ. ᴜsᴇ ʏᴏᴜʀ <b>ғʀᴇᴇ ᴛʀɪᴇs</b> ᴏʀ ɢᴏ <b>ᴘʀᴇᴍɪᴜᴍ</b> ғᴏʀ ᴜɴʟɪᴍɪᴛᴇᴅ ᴀᴄᴄᴇss. sɪᴍᴘʟʏ sᴇɴᴅ ᴀ ɴᴜᴍʙᴇʀ (ᴇ.ɢ., <code>+919876543210</code>) ᴛᴏ sᴛᴀʀᴛ sᴇᴀʀᴄʜɪɴɢ!</blockquote></b>")
FORCE_MSG = os.environ.get("FORCE_SUB_MESSAGE", "ʜᴇʟʟᴏ {mention}\n\n<b><blockquote>ᴊᴏɪɴ ᴏᴜʀ ᴄʜᴀɴɴᴇʟs ᴀɴᴅ ᴛʜᴇɴ ᴄʟɪᴄᴋ ᴏɴ ʀᴇʟᴏᴀᴅ button ᴛᴏ ɢᴇᴛ ʏᴏᴜʀ ʀᴇǫᴜᴇꜱᴛᴇᴅ ꜰɪʟᴇ.</b></blockquote>")

CMD_TXT = """<blockquote><b>» ᴀᴅᴍɪɴ ᴄᴏᴍᴍᴀɴᴅs:</b></blockquote>

<b>›› /dlt_time :</b> sᴇᴛ ᴀᴜᴛᴏ ᴅᴇʟᴇᴛᴇ ᴛɪᴍᴇ
<b>›› /check_dlt_time :</b> ᴄʜᴇᴄᴋ ᴄᴜʀʀᴇɴᴛ ᴅᴇʟᴇᴛᴇ ᴛɪᴍᴇ
<b>›› /dbroadcast :</b> ʙʀᴏᴀᴅᴄᴀsᴛ ᴅᴏᴄᴜᴍᴇɴᴛ / ᴠɪᴅᴇᴏ
<b>›› /ban :</b> ʙᴀɴ ᴀ ᴜꜱᴇʀ
<b>›› /unban :</b> ᴜɴʙᴀɴ ᴀ ᴜꜱᴇʀ
<b>›› /banlist :</b> ɢᴇᴛ ʟɪsᴛ ᴏꜰ ʙᴀɴɴᴇᴅ ᴜꜱᴇʀs
<b>›› /addchnl :</b> ᴀᴅᴅ ꜰᴏʀᴄᴇ sᴜʙ ᴄʜᴀɴɴᴇʟ
<b>›› /delchnl :</b> ʀᴇᴍᴏᴠᴇ ꜰᴏʀᴄᴇ sᴜʙ ᴄʜᴀɴɴᴇʟ
<b>›› /listchnl :</b> ᴠɪᴇᴡ ᴀᴅᴅᴇᴅ ᴄʜᴀɴɴᴇʟs
<b>›› /fsub_mode :</b> ᴛᴏɢɢʟᴇ ꜰᴏʀᴄᴇ sᴜʙ ᴍᴏᴅᴇ
<b>›› /pbroadcast :</b> sᴇɴᴅ ᴘʜᴏᴛᴏ ᴛᴏ ᴀʟʟ ᴜꜱᴇʀs
<b>›› /add_admin :</b> ᴀᴅᴅ ᴀɴ ᴀᴅᴍɪɴ
<b>›› /deladmin :</b> ʀᴇᴍᴏᴠᴇ ᴀɴ ᴀᴅᴍɪɴ
<b>›› /admins :</b> ɢᴇᴛ ʟɪsᴛ ᴏꜰ ᴀᴅᴍɪɴs
<b>›› /delreq :</b> Rᴇᴍᴏᴠᴇᴅ ʟᴇғᴛᴏᴠᴇʀ ɴᴏɴ-ʀᴇǫᴜᴇsᴛ ᴜsᴇʀs
"""
#--------------------------------------------
CUSTOM_CAPTION = os.environ.get("CUSTOM_CAPTION", "<b>• ʙʏ @SayXSee_Dev</b>") #set your Custom Caption here, Keep None for Disable Custom Caption
PROTECT_CONTENT = True if os.environ.get('PROTECT_CONTENT', "False") == "True" else False #set True if you want to prevent users from forwarding files from bot
#--------------------------------------------
#Set true if you want Disable your Channel Posts Share button
DISABLE_CHANNEL_BUTTON = os.environ.get("DISABLE_CHANNEL_BUTTON", None) == 'True'
#--------------------------------------------
BOT_STATS_TEXT = "<b>BOT UPTIME</b>\n{uptime}"
USER_REPLY_TEXT = "ʙᴀᴋᴋᴀ ! ʏᴏᴜ ᴀʀᴇ ɴᴏᴛ ᴍʏ ꜱᴇɴᴘᴀɪ!!"
#--------------------------------------------


LOG_FILE_NAME = "filesharingbot.txt"

logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s - %(levelname)s] - %(name)s - %(message)s",
    datefmt='%d-%b-%y %H:%M:%S',
    handlers=[
        RotatingFileHandler(
            LOG_FILE_NAME,
            maxBytes=50000000,
            backupCount=10
        ),
        logging.StreamHandler()
    ]
)
logging.getLogger("pyrogram").setLevel(logging.WARNING)


def LOGGER(name: str) -> logging.Logger:
    return logging.getLogger(name)
   
