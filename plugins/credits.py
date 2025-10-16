import asyncio
from pyrogram import Client, filters
from pyrogram.types import Message
from pyrogram.enums import ParseMode
from bot import Bot 
from config import ADMINS # Ensure ADMINS list is defined in config.py
from database.database import db

# Admin filter
admin = filters.user(ADMINS) if ADMINS else filters.user(0)

# ==============================================================================
# /add_credits: Add credits to a user's account
# ==============================================================================

@Bot.on_message(filters.command('add_credits') & filters.private & admin)
async def add_custom_credits_command(client: Client, msg: Message):
    """
    Usage: /add_credits <user_id> <credit_count>
    Adds a specified number of search credits to a user's account.
    """
    if len(msg.command) != 3:
        # Polished: Ensure blockquote is used
        await msg.reply_text("<b><blockquote>💡 ᴜsᴀɢᴇ: <code>/add_credits &lt;ᴜsᴇʀ_ɪᴅ&gt; &lt;ᴄʀᴇᴅɪᴛ_ᴄᴏᴜɴᴛ&gt;</code>\n\nᴇxᴀᴍᴘʟᴇ: <code>/add_credits 1234567 100</code></blockquote></b>", parse_mode=ParseMode.HTML)
        return
    
    try:
        user_id = int(msg.command[1])
        credit_count = int(msg.command[2])

        if credit_count <= 0:
            return await msg.reply_text("<b><blockquote>❌ ᴄʀᴇᴅɪᴛ ᴄᴏᴜɴᴛ ᴍᴜsᴛ ʙᴇ ᴀ ᴘᴏsɪᴛɪᴠᴇ ɴᴜᴍʙᴇʀ.</blockquote></b>", parse_mode=ParseMode.HTML)

        # 1. Add credits to the database (This function handles adding the new count to the existing tries)
        await db.add_referral_credits(user_id, credit_count) 

        # 2. Admin Confirmation Message
        await msg.reply_text(
            f"<b><blockquote>✅ {credit_count} ᴄʀᴇᴅɪᴛs ᴀᴅᴅᴇᴅ ᴛᴏ ᴜsᴇʀ <code>{user_id}</code>.</blockquote></b>",
            parse_mode=ParseMode.HTML
        )

        # 3. Notify the User (Optional but good UX)
        try:
            current_tries, _, _ = await db.get_user_status(user_id)
            await client.send_message(
                chat_id=user_id,
                text=(
                    f"🎉 **ᴄʀᴇᴅɪᴛs ʀᴇᴄᴇɪᴠᴇᴅ!**\n\n"
                    f"ᴀᴅᴍɪɴ ʜᴀs ᴀᴅᴅᴇᴅ **{credit_count} ɴᴇᴡ sᴇᴀʀᴄʜ ᴄʀᴇᴅɪᴛs** ᴛᴏ ʏᴏᴜʀ ᴀᴄᴄᴏᴜɴᴛ.\n"
                    f"ʏᴏᴜʀ ɴᴇᴡ ʙᴀʟᴀɴᴄᴇ ɪs: **{current_tries}**."
                ),
                parse_mode=ParseMode.HTML
            )
        except Exception as e:
            print(f"Failed to notify user {user_id} after adding credits: {e}")

    except ValueError:
        await msg.reply_text("<b><blockquote>❌ ɪɴᴠᴀʟɪᴅ ɪɴᴘᴜᴛ. ᴜsᴇʀ ɪᴅ ᴀɴᴅ ᴄʀᴇᴅɪᴛ ᴄᴏᴜɴᴛ ᴍᴜsᴛ ʙᴇ ᴡʜᴏʟᴇ ɴᴜᴍʙᴇʀs.</blockquote></b>", parse_mode=ParseMode.HTML)
    except Exception as e:
        await msg.reply_text(f"<b><blockquote>⚠️ ᴀɴ ᴇʀʀᴏʀ ᴏᴄᴄᴜʀʀᴇᴅ: <code>{str(e)}</code></blockquote></b>", parse_mode=ParseMode.HTML)


# ==============================================================================
# /rem_credits: Remove credits from a user's account
# ==============================================================================

@Bot.on_message(filters.command('rem_credits') & filters.private & admin)
async def remove_custom_credits_command(client: Client, msg: Message):
    """
    Usage: /rem_credits <user_id> <credit_count>
    Removes a specified number of search credits from a user's account.
    """
    if len(msg.command) != 3:
        
        await msg.reply_text("<b><blockquote>💡 ᴜsᴀɢᴇ: <code>/rem_credits &lt;ᴜsᴇʀ_ɪᴅ&gt; &lt;ᴄʀᴇᴅɪᴛ_ᴄᴏᴜɴᴛ&gt;</code>\n\nᴇxᴀᴍᴘʟᴇ: <code>/rem_credits 1234567 50</code></blockquote></b>", parse_mode=ParseMode.HTML)
        return

    try:
        user_id = int(msg.command[1])
        credit_count = int(msg.command[2])

        if credit_count <= 0:
            return await msg.reply_text("<b><blockquote>❌ ᴄʀᴇᴅɪᴛ ᴄᴏᴜɴᴛ ᴍᴜsᴛ ʙᴇ ᴀ ᴘᴏsɪᴛɪᴠᴇ ɴᴜᴍʙᴇʀ.</blockquote></b>", parse_mode=ParseMode.HTML)

        
        await db.add_referral_credits(user_id, -credit_count)
        
        # 2. Admin Confirmation Message
        await msg.reply_text(
            f"<b><blockquote>✅ {credit_count} ᴄʀᴇᴅɪᴛs ʀᴇᴍᴏᴠᴇᴅ ғʀᴏᴍ ᴜsᴇʀ <code>{user_id}</code>.</blockquote></b>",
            parse_mode=ParseMode.HTML
        )

        # 3. Notify the User (Optional)
        try:
            current_tries, _, _ = await db.get_user_status(user_id)
            await client.send_message(
                chat_id=user_id,
                text=(
                    f"⚠️ **ᴄʀᴇᴅɪᴛ ᴅᴇᴅᴜᴄᴛɪᴏɴ ɴᴏᴛɪᴄᴇ!**\n\n"
                    f"ᴀᴅᴍɪɴ ʜᴀs ʀᴇᴍᴏᴠᴇᴅ **{credit_count} sᴇᴀʀᴄʜ ᴄʀᴇᴅɪᴛs** ғʀᴏᴍ ʏᴏᴜʀ ᴀᴄᴄᴏᴜɴᴛ.\n"
                    f"ʏᴏᴜʀ ɴᴇᴡ ʙᴀʟᴀɴᴄᴇ ɪs: **{current_tries}**."
                ),
                parse_mode=ParseMode.HTML
            )
        except Exception as e:
            print(f"Failed to notify user {user_id} after removing credits: {e}")

    except ValueError:
        await msg.reply_text("<b><blockquote>❌ ɪɴᴠᴀʟɪᴅ ɪɴᴘᴜᴛ. ᴜsᴇʀ ɪᴅ ᴀɴᴅ ᴄʀᴇᴅɪᴛ ᴄᴏᴜɴᴛ ᴍᴜsᴛ ʙᴇ ᴡʜᴏʟᴇ ɴᴜᴍʙᴇʀs.</blockquote></b>", parse_mode=ParseMode.HTML)
    except Exception as e:
        await msg.reply_text(f"<b><blockquote>⚠️ ᴀɴ ᴇʀʀᴏʀ ᴏᴄᴄᴜʀʀᴇᴅ: <code>{str(e)}</code></blockquote></b>", parse_mode=ParseMode.HTML)
