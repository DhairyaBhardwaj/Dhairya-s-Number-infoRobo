import secrets
from pyrogram import Client, filters
from pyrogram.enums import ParseMode
from pyrogram.types import Message
from database.database import db 
from config import ADMINS 
import asyncio
import re

# Admin filter
admin = filters.user(ADMINS) if ADMINS else filters.user(0) 

# --- DATABASE INTERACTION HELPER (Uses functions from database.py) ---

async def increment_redeem_usage_and_mark_user(code: str, user_id: int, credits_gained: int) -> bool:
    """
    1. Increments the used count for the code.
    2. Marks the user as having redeemed the code.
    3. Adds credits to the user's account via db.add_referral_credits.
    """
    try:
        code_data = await db.get_redeem_code(code)
        if not code_data:
            return False
            
        new_used_count = code_data.get("used_count", 0) + 1
        
        
        used_by_list = code_data.get("used_by", [])
        used_by_list.append(user_id)
        
        
        await db.update_redeem_code(code, {
            "used_count": new_used_count,
            "used_by": used_by_list,
        })
        
        # Add credits to the user (add_referral_credits adds to the total count)
        await db.add_referral_credits(user_id, credits_gained)

        return True
    except Exception as e:
        print(f"ᴇʀʀᴏʀ ᴜᴘᴅᴀᴛɪɴɢ ʀᴇᴅᴇᴇᴍ ᴄᴏᴅᴇ {code} ᴏʀ ᴀᴅᴅɪɴɢ ᴄʀᴇᴅɪᴛs: {e}")
        return False

# --- ADMIN COMMAND: CREATE REDEEM CODE ---

@Client.on_message(filters.command("add_redeem") & filters.private & admin)
async def add_redeem_command(client: Client, message: Message):
    """
    ᴄʀᴇᴀᴛᴇs ᴀ ɴᴇᴡ ʀᴇᴅᴇᴇᴍ ᴄᴏᴅᴇ.
    ᴜsᴀɢᴇ: /add_redeem <credits_per_user> <max_users>
    """
    
    parts = message.text.split()
    
    if len(parts) != 3 or not parts[1].isdigit() or not parts[2].isdigit():
        return await message.reply_text(
            "<b><blockquote>⚠️ ɪɴᴠᴀʟɪᴅ ᴜsᴀɢᴇ.\n"
            "ᴜsᴀɢᴇ: <code>/add_redeem <ᴄʀᴇᴅɪᴛs_ᴘᴇʀ_ᴜsᴇʀ> <ᴍᴀx_ᴜsᴇʀs></code>\n"
            "ᴇ.ɢ., <code>/add_redeem 2 50</code> (ғɪʀsᴛ 50 ᴜsᴇʀs ɢᴇᴛ 2 ᴄʀᴇᴅɪᴛs ᴇᴀᴄʜ)</blockquote></b>",
            parse_mode=ParseMode.HTML
        )
        
    try:
        credits_to_give = int(parts[1])
        max_uses = int(parts[2])
    except ValueError:
        return await message.reply_text(
            "<b><blockquote>⚠️ ᴄʀᴇᴅɪᴛs ᴀɴᴅ ᴜsᴇʀs ᴍᴜsᴛ ʙᴇ ɴᴜᴍʙᴇʀs.</blockquote></b>",
            parse_mode=ParseMode.HTML
        )
        
    if credits_to_give <= 0 or max_uses <= 0:
        return await message.reply_text(
            "<b><blockquote>⚠️ ᴄʀᴇᴅɪᴛs ᴀɴᴅ ᴜsᴇʀs ᴍᴜsᴛ ʙᴇ ɢʀᴇᴀᴛᴇʀ ᴛʜᴀɴ ᴢᴇʀᴏ.</blockquote></b>",
            parse_mode=ParseMode.HTML
        )

    # Generate unique code: SayXSee_ + 10 random URL-safe characters
    code_suffix = secrets.token_urlsafe(10)
    new_code = f"SayXSee_{code_suffix}"
    
    # Data to be stored in the 'redeem_codes' collection
    code_data = {
        "credits": credits_to_give,
        "max_uses": max_uses,
        "used_count": 0,
        "used_by": [], 
        "is_active": True
    }
    
    if await db.add_redeem_code(new_code, code_data):
        response_text = f"🎉 ʀᴇᴅᴇᴇᴍ ᴄᴏᴅᴇ ᴄʀᴇᴀᴛᴇᴅ sᴜᴄᴄᴇssғᴜʟʟʏ!\n\n"
        response_text += f"ᴄᴏᴅᴇ ɪᴅ: <code>/get_redeem {new_code}</code>\n"
        response_text += f"ᴄʀᴇᴅɪᴛs ᴘᴇʀ ᴜsᴇʀ: {credits_to_give}\n"
        response_text += f"ᴍᴀxɪᴍᴜᴍ ᴜsᴇs: {max_uses}\n"
        response_text += f"sʜᴀʀᴇ ᴛʜɪs ᴄᴏᴅᴇ ᴡɪᴛʜ ᴜsᴇʀs ᴛᴏ ʟᴇᴛ ᴛʜᴇᴍ ʀᴇᴅᴇᴇᴍ."
        
        await message.reply_text(
            f"<b><blockquote>{response_text}</blockquote></b>",
            parse_mode=ParseMode.HTML
        )
    else:
        await message.reply_text(
            "<b><blockquote>❌ ᴇʀʀᴏʀ ɪɴ ᴄʀᴇᴀᴛɪɴɢ ᴄᴏᴅᴇ ɪɴ ᴅᴀᴛᴀʙᴀsᴇ. ᴄʜᴇᴄᴋ ʟᴏɢs.</blockquote></b>",
            parse_mode=ParseMode.HTML
        )

# --- USER COMMAND: REDEEM CODE ---

@Client.on_message(filters.command("get_redeem") & filters.private)
async def get_redeem_command(client: Client, message: Message):
    """
    ᴀʟʟᴏᴡs ᴜsᴇʀs ᴛᴏ ʀᴇᴅᴇᴇᴍ ᴀ sᴘᴇᴄɪᴀʟ ᴄᴏᴅᴇ ғᴏʀ ᴄʀᴇᴅɪᴛs.
    ᴜsᴀɢᴇ: /get_redeem <code_id>
    """
    
    parts = message.text.split()
    user_id = message.from_user.id

    if len(parts) != 2:
        return await message.reply_text(
            "<b><blockquote>⚠️ ɪɴᴠᴀʟɪᴅ ᴜsᴀɢᴇ.\n"
            "ᴜsᴀɢᴇ: <code>/get_redeem <ᴄᴏᴅᴇ_ɪᴅ></code>\n"
            "ᴇ.ɢ., <code>/get_redeem SayXSee_wanj18xn2</code></blockquote></b>",
            parse_mode=ParseMode.HTML
        )
        
    code_to_redeem = parts[1].strip()
    code_data = await db.get_redeem_code(code_to_redeem)
    
    if not code_data or not code_data.get("is_active", True):
        return await message.reply_text(
            "<b><blockquote>❌ ɪɴᴠᴀʟɪᴅ ᴏʀ ɪɴᴀᴄᴛɪᴠᴇ ʀᴇᴅᴇᴇᴍ ᴄᴏᴅᴇ. ᴅᴏᴜʙʟᴇ-ᴄʜᴇᴄᴋ ᴛʜᴇ ᴄᴏᴅᴇ ᴀɴᴅ ᴛʀʏ ᴀɢᴀɪɴ.</blockquote></b>",
            parse_mode=ParseMode.HTML
        )

    # --- 1. Check if already redeemed ---
    
    used_by = code_data.get("used_by", [])
    if user_id in used_by:
        return await message.reply_text(
            "<b><blockquote>⚠️ ʏᴏᴜ ʜᴀᴠᴇ ᴀʟʀᴇᴀᴅʏ ʀᴇᴅᴇᴇᴍᴇᴅ ᴛʜɪs ᴄᴏᴅᴇ. ᴏɴᴇ ᴜsᴇ ᴘᴇʀ ᴜsᴇʀ.</blockquote></b>",
            parse_mode=ParseMode.HTML
        )

    # --- 2. Check for maximum uses ---
    max_uses = code_data.get("max_uses", 0)
    used_count = code_data.get("used_count", 0)
    credits_gained = code_data.get("credits", 0)
    
    if used_count >= max_uses:
        
        return await message.reply_text(
            "<b><blockquote>❌ ᴛʜɪs ʀᴇᴅᴇᴇᴍ ᴄᴏᴅᴇ ʜᴀs ʀᴇᴀᴄʜᴇᴅ ɪᴛs ᴍᴀxɪᴍᴜᴍ ᴜsᴀɢᴇ ʟɪᴍɪᴛ. ɪᴛ ɪs ɴᴏᴡ ᴇxᴘɪʀᴇᴅ.</blockquote></b>",
            parse_mode=ParseMode.HTML
        )

    # --- 3. Redeem the code ---
    if await increment_redeem_usage_and_mark_user(code_to_redeem, user_id, credits_gained):
        
        # Get updated status for response clarity
        
        daily_tries, is_premium, _ = await db.get_user_status(user_id) 
        new_total = 'ᴜɴʟɪᴍɪᴛᴇᴅ' if is_premium else daily_tries

        success_text = f"✅ sᴜᴄᴄᴇss! ʏᴏᴜ ʜᴀᴠᴇ ʀᴇᴅᴇᴇᴍᴇᴅ ᴛʜᴇ ᴄᴏᴅᴇ.\n\n"
        success_text += f"🎉 ᴄʀᴇᴅɪᴛs ᴀᴅᴅᴇᴅ: <b>{credits_gained}</b>\n"
        success_text += f"💰 ʏᴏᴜʀ ɴᴇᴡ ᴛᴏᴛᴀʟ ᴄʀᴇᴅɪᴛs: {new_total}\n"
        success_text += f"📊 ᴄᴏᴅᴇ ᴜsᴀɢᴇ: {used_count + 1} / {max_uses}"
        
        await message.reply_text(
            f"<b><blockquote>{success_text}</blockquote></b>",
            parse_mode=ParseMode.HTML
        )
    else:
        await message.reply_text(
            "<b><blockquote>❌ ғᴀɪʟᴇᴅ ᴛᴏ ʀᴇᴅᴇᴇᴍ. ᴀɴ ɪɴᴛᴇʀɴᴀʟ ᴇʀʀᴏʀ ᴏᴄᴄᴜʀʀᴇᴅ. ᴘʟᴇᴀsᴇ ᴛʀʏ ᴀɢᴀɪɴ ʟᴀᴛᴇʀ.</blockquote></b>",
            parse_mode=ParseMode.HTML
        )
