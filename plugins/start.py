import os
import re
from datetime import datetime, timedelta
import httpx 

from pyrogram import Client, filters, __version__
from pyrogram.enums import ParseMode, ChatAction
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from pyrogram.errors import FloodWait, UserIsBlocked, InputUserDeactivated, UserNotParticipant
from bot import Bot
from config import *
from helper_func import *
from database.database import *
from database.db_premium import *
from plugins.search import lookup_number_info, format_search_results 
from plugins.premium import *

# =====================================================================================
# CONFIGURATION & HELPER FUNCTIONS
# =====================================================================================

BAN_SUPPORT = f"{BAN_SUPPORT}"
CHANNELS_PER_PAGE = 3  # Configuration for pagination

def is_valid_phone_number(text: str) -> str or None:
    """
    Checks if the text is a valid Indian phone number.
    It must start with an optional '+' followed by '91', and then exactly 10 digits.
    """
    # Regex: Optional '+' followed by '91', followed by exactly 10 digits.
    match = re.fullmatch(r'^\+?91(\d{10})$', text.strip())
    if match:
        # Returns the number (with '+' if present)
        return match.group(0) 
    return None

# List of ALL commands defined for the negation filter (RESTORED TO FULL LIST)
ALL_BOT_COMMANDS = [
    'start', 'referral', 'credits', 'getplan', 'addpremium', 
    'remove_premium', 'premium_users', 'commands', 'about', 'help', 'myplan',

    # auto delete
    'dlt_time', 'check_dlt_time',

    # broadcast
    'dbroadcast', 'pbroadcast',

    # ban system
    'ban', 'unban', 'banlist',

    # force subscribe
    'addchnl', 'delchnl', 'listchnl', 'fsub_mode',

    # admin system
    'add_admin', 'deladmin', 'admins', 'stats', 'users',

    # clean-up
    'delreq'
]

# Admin filter used in other commands
admin = filters.user(ADMINS) if ADMINS else filters.user(0) 

# Global cache for channel data to avoid repeated API calls
chat_data_cache = {} 

async def get_fsub_buttons(client: Client, user_id: int, all_channels: list, page: int = 0):
    """Generates the InlineKeyboardMarkup for the FSUB message with pagination."""
    
    start_index = page * CHANNELS_PER_PAGE
    end_index = start_index + CHANNELS_PER_PAGE
    channels_to_show = all_channels[start_index:end_index]
    
    buttons = []
    has_unsubscribed_channel = False

    for chat_id in channels_to_show:
        mode = await db.get_channel_mode(chat_id)

        if not await is_sub(client, user_id, chat_id):
            has_unsubscribed_channel = True
            try:
                if chat_id in chat_data_cache:
                    data = chat_data_cache[chat_id]
                else:
                    data = await client.get_chat(chat_id)
                    chat_data_cache[chat_id] = data

                name = data.title
                link = None

                # Logic to determine link type
                if data.username:
                    link = f"https://t.me/{data.username}"
                elif mode == "on":
                    # Private channel with join request enabled
                    invite = await client.create_chat_invite_link(
                        chat_id=chat_id,
                        creates_join_request=True,
                        expire_date=datetime.utcnow() + timedelta(seconds=FSUB_LINK_EXPIRY) if FSUB_LINK_EXPIRY else None
                    )
                    link = invite.invite_link
                else:
                    # Private channel with no username and no join request (standard invite link)
                    invite = await client.create_chat_invite_link(
                        chat_id=chat_id,
                        expire_date=datetime.utcnow() + timedelta(seconds=FSUB_LINK_EXPIRY) if FSUB_LINK_EXPIRY else None
                    )
                    link = invite.invite_link

                if link:
                    buttons.append([InlineKeyboardButton(text=name, url=link)])

            except Exception as e:
                print(f"Error creating FSUB button for chat {chat_id}: {e}")
                # Skip this channel if an error occurs

    # --- Pagination Buttons ---
    nav_buttons = []
    total_pages = (len(all_channels) + CHANNELS_PER_PAGE - 1) // CHANNELS_PER_PAGE

    if page > 0:
        nav_buttons.append(InlineKeyboardButton(text="« ᴘʀᴇᴠɪᴏᴜs", callback_data=f"fsub_page_{page-1}"))

    # Add a spacer if only one button is present, to center it
    if len(nav_buttons) > 0 and page + 1 >= total_pages:
        pass # Not necessary, can let it align left

    if page + 1 < total_pages:
        nav_buttons.append(InlineKeyboardButton(text="ɴᴇxᴛ »", callback_data=f"fsub_page_{page+1}"))

    if nav_buttons:
        buttons.append(nav_buttons)

    # --- Retry Button (Added only on the last row for clean look) ---
    if has_unsubscribed_channel:
        # Determine the payload for the /start command if available, otherwise just /start
        try:
            retry_payload = message.command[1] if message and len(message.command) > 1 else ""
            retry_url = f"https://t.me/{client.username}?start={retry_payload}"
        except:
            retry_url = f"https://t.me/{client.username}?start"

        buttons.append([InlineKeyboardButton(text='♻️ ᴛʀʏ ᴀɢᴀɪɴ', url=retry_url)])

    return InlineKeyboardMarkup(buttons)


# =====================================================================================
# REUSABLE CONTENT FUNCTIONS (Called by commands AND callbacks)
# =====================================================================================

async def send_referral_info(client: Client, user_id: int, message: Message = None, callback: CallbackQuery = None):
    """Sends the referral link and stats, now with a 'Copy Link' button."""
    
    target = message or callback.message
    bot_username = client.username 
    if not bot_username:
        return await target.reply_text("<b><blockquote>⚠️ ʙᴏᴛ ᴜsᴇʀɴᴀᴍᴇ ɴᴏᴛ sᴇᴛ. ᴄᴀɴɴᴏᴛ ɢᴇɴᴇʀᴀᴛᴇ ʀᴇғᴇʀʀᴀʟ ʟɪɴᴋ.</blockquote></b>", parse_mode=ParseMode.HTML)
        
    referral_link = f"https://t.me/{bot_username}?start=ref_{user_id}"
    
    referrals = await db.get_referral_count(user_id)
    daily_tries, is_premium, _ = await db.get_user_status(user_id)
    
    status_text = "👑 ᴘʀᴇᴍɪᴜᴍ (ᴜɴʟɪᴍɪᴛᴇᴅ)" if is_premium else f"🆓 ғʀᴇᴇ ({daily_tries} ʟᴇғᴛ)"
    
    text = f"🔗 ʏᴏᴜʀ ʀᴇғᴇʀʀᴀʟ ʟɪɴᴋ:\n <code>{referral_link}</code> \n\n"
    text += f"🤝 ʜᴏᴡ ɪᴛ ᴡᴏʀᴋs: sʜᴀʀᴇ ᴛʜɪs ʟɪɴᴋ. ᴡʜᴇɴ ᴀ ɴᴇᴡ ᴜsᴇʀ ᴊᴏɪɴs ᴛʜᴇ ʙᴏᴛ ᴜsɪɴɢ ʏᴏᴜʀ ʟɪɴᴋ ᴀɴᴅ ᴄᴏᴍᴘʟᴇᴛᴇs ғsᴜʙ, ʏᴏᴜ ɪɴsᴛᴀɴᴛʟʏ ɢᴇᴛ 2 ᴇxᴛʀᴀ ғʀᴇᴇ sᴇᴀʀᴄʜᴇs.\n\n"
    text += f"📊 ʏᴏᴜʀ sᴛᴀᴛs:\n"
    text += f"ᴄᴜʀʀᴇɴᴛ sᴛᴀᴛᴜs: {status_text}\n"
    text += f"ᴛᴏᴛᴀʟ sᴜᴄᴄᴇssғᴜʟ ʀᴇғᴇʀʀᴀʟs: {referrals}"

    # NEW: Add a button to copy/share the link
    buttons = [
        [InlineKeyboardButton("🔗 ᴄᴏᴘʏ/sʜᴀʀᴇ ʟɪɴᴋ", url=f"https://telegram.me/share/url?url={referral_link}")]
    ]
    
    # Check if we are responding to a command or a callback
    if callback:
        await callback.message.edit_text(
            f"<b><blockquote>{text}</blockquote></b>", 
            reply_markup=InlineKeyboardMarkup(buttons),
            parse_mode=ParseMode.HTML
        )
    else:
        await target.reply_text(
            f"<b><blockquote>{text}</blockquote></b>", 
            reply_markup=InlineKeyboardMarkup(buttons),
            parse_mode=ParseMode.HTML
        )


async def send_plan_and_credits_info(user_id: int, message: Message = None, callback: CallbackQuery = None):
    """Sends the user's credit status and plan info."""
    
    daily_tries, is_premium, _ = await db.get_user_status(user_id)
    premium_expiry = await db.get_premium_expiry(user_id)
    
    if is_premium:
        expiry_str = premium_expiry.strftime('%Y-%m-%d %H:%M:%S') if premium_expiry else "ɴ/ᴀ (ᴘᴇʀᴍᴀɴᴇɴᴛ)"
        status_text = f"👑 ᴘʀᴇᴍɪᴜᴍ ᴜsᴇʀ\nᴇxᴘɪʀᴇs ᴏɴ: {expiry_str}" 
        remaining_text = "ᴜɴʟɪᴍɪᴛᴇᴅ (ᴘʀᴇᴍɪᴜᴍ)"
    else:
        status_text = "🆓 ғʀᴇᴇ ᴜsᴇʀ"
        remaining_text = f"{daily_tries}"

    text = f"💰 ʏᴏᴜʀ ᴄᴜʀʀᴇɴᴛ sᴛᴀᴛᴜs & ᴄʀᴇᴅɪᴛs\n\n" 
    text += f"— — — — — — — — — — — —\n"
    text += f"{status_text}\n"
    text += f"— — — — — — — — — — — —\n"
    text += f"ᴅᴀɪʟʏ ғʀᴇᴇ ᴛʀɪᴇs ʀᴇᴍᴀɪɴɪɴɢ: {remaining_text}\n"
    text += f"*(ғʀᴇᴇ ᴛʀɪᴇs ʀᴇsᴇᴛ ᴅᴀɪʟʏ ᴛᴏ 2)*\n\n"
    text += f"ᴡᴀɴᴛ ᴍᴏʀᴇ? ᴜsᴇ /referral ᴏʀ ᴄʜᴇᴄᴋ /getplan."
    
    target = message or callback.message
    await target.reply_text(f"<b><blockquote>{text}</blockquote></b>", parse_mode=ParseMode.HTML)


# =====================================================================================
# CORE BOT COMMANDS & HANDLERS
# =====================================================================================

@Bot.on_message(filters.command('start') & filters.private)
async def start_command(client: Client, message: Message):
    user_id = message.from_user.id
    text = message.text
    
    # --- 1. Ban Check (FIRST GATE) ---
    banned_users = await db.get_ban_users()
    if user_id in banned_users:
        return await message.reply_text(
            "<b><blockquote>⛔️ ʏᴏᴜ ᴀʀᴇ ʙᴀɴɴᴇᴅ ғʀᴏᴍ ᴜsɪɴɢ ᴛʜɪs ʙᴏᴛ.</b>\n\n"
            "<i>ᴄᴏɴᴛᴀᴄᴛ sᴜᴘᴘᴏʀᴛ ɪғ ʏᴏᴜ ᴛʜɪɴᴋ ᴛʜɪs ɪs ᴀ ᴍɪsᴛᴀᴋᴇ.</i></blockquote></b>",
            reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton("ᴄᴏɴᴛᴀᴄᴛ sᴜᴘᴘᴏʀᴛ", url=BAN_SUPPORT)]]
            ),
            parse_mode=ParseMode.HTML
        )
    
    # --- 2. Force Subscription Check (SECOND GATE) ---
    # Pass the message object to not_joined so it can extract the payload for retry logic
    if not await is_subscribed(client, user_id):
        return await not_joined(client, message)

    # --- 3. Referral Payload & Registration Processing (Runs ONLY AFTER FSUB) ---
    referrer_id = None
    if len(text.split()) > 1:
        payload = text.split(" ", 1)[1]
        
        if payload.startswith("ref_"):
            try:
                referrer_id = int(payload.split("ref_")[1])
            except ValueError:
                referrer_id = None
                
    is_new_user = not await db.present_user(user_id)
    if is_new_user:
        await db.add_user_with_referrer(user_id, referrer_id) 
        
        current_tries, _, _ = await db.get_user_status(user_id)
        if current_tries == 0:
             await db.add_referral_credits(user_id, 2) 
        
        if referrer_id:
            await db.add_referral_credits(referrer_id, 2)
            await db.update_referral_count(referrer_id, 1)

            try:
                # Notify referrer and show their updated total credits
                referrer_tries, referrer_is_premium, _ = await db.get_user_status(referrer_id)
                status_text = "ᴘʀᴇᴍɪᴜᴍ (ᴜɴʟɪᴍɪᴛᴇᴅ)" if referrer_is_premium else f"{referrer_tries} ᴛʀɪᴇs ʟᴇғᴛ"

                await client.send_message(
                    referrer_id,
                    f"<b><blockquote>🎉 ʀᴇғᴇʀʀᴀʟ sᴜᴄᴄᴇss!</b>\n"
                    f"ᴏɴᴇ ɴᴇᴡ ᴜsᴇʀ ᴊᴏɪɴᴇᴅ ᴜsɪɴɢ ʏᴏᴜʀ ʟɪɴᴋ. ʏᴏᴜ'ᴠᴇ ʙᴇᴇɴ ʀᴇᴡᴀʀᴅᴇᴅ ᴡɪᴛʜ 2 ᴇxᴛʀᴀ ғʀᴇᴇ sᴇᴀʀᴄʜᴇs!\n"
                    f"ʏᴏᴜʀ ɴᴇᴡ sᴛᴀᴛᴜs: {status_text}</blockquote></b>",
                    parse_mode=ParseMode.HTML
                )
            except Exception as e:
                # Use logging in a real environment
                print(f"Failed to notify referrer {referrer_id}: {e}")
    else:
        # Ensures user is in the database even if the new_user check was faulty
        if not await db.present_user(user_id):
            try:
                await db.add_user(user_id)
            except:
                pass


    # --- 4. Final Welcome Message ---
    reply_markup = InlineKeyboardMarkup(
        [
                [InlineKeyboardButton("• ᴍᴏʀᴇ ᴄʜᴀɴɴᴇʟs •", url="https://t.me/Movies8777")],
                [InlineKeyboardButton("🔗 ʀᴇғᴇʀ & ᴇᴀʀɴ", callback_data="show_referral_info"),
                 InlineKeyboardButton("💰 ʙᴜʏ ᴄʀᴇᴅɪᴛs", callback_data="premium")],
                [InlineKeyboardButton("• ᴀʙᴏᴜᴛ", callback_data = "about"),
                 InlineKeyboardButton('ʜᴇʟᴘ •', callback_data = "help")]
        ]
    )
    
    daily_tries, is_premium, _ = await db.get_user_status(user_id) 
    status = "👑 ᴘʀᴇᴍɪᴜᴍ (ᴜɴʟɪᴍɪᴛᴇᴅ)" if is_premium else f"🆓 ғʀᴇᴇ ({daily_tries} ᴛʀɪᴇs ʟᴇғᴛ)"

    welcome_caption_text = START_MSG.format(
        first=message.from_user.first_name,
        last=message.from_user.last_name,
        username=None if not message.from_user.username else '@' + message.from_user.username,
        mention=message.from_user.mention,
        id=message.from_user.id
    ) + f"\n\nʏᴏᴜʀ sᴛᴀᴛᴜs: {status}\n\nᴛᴏ sᴇᴀʀᴄʜ: sɪᴍᴘʟʏ sᴇɴᴅ ᴀ ᴘʜᴏɴᴇ ɴᴜᴍʙᴇʀ (e.g., <code>+911234567890</code>)." 

    final_caption = f"<b><blockquote>{welcome_caption_text}</blockquote></b>" 

    await message.reply_photo(
        photo=START_PIC,
        caption=final_caption, 
        reply_markup=reply_markup,
        parse_mode=ParseMode.HTML, 
        message_effect_id=5104841245755180586
    ) 


@Bot.on_message(filters.private & filters.text & ~filters.command(ALL_BOT_COMMANDS))
async def number_search_handler(client: Client, message: Message):
    user_id = message.from_user.id
    search_query = is_valid_phone_number(message.text)
    
    if not search_query:
        return await message.reply_text(
            "<b><blockquote>⚠️ ᴘʟᴇᴀsᴇ ᴇɴᴛᴇʀ ᴀ ᴠᴀʟɪᴅ ɪɴᴅɪᴀɴ ᴘʜᴏɴᴇ ɴᴜᴍʙᴇʀ, sᴛᴀʀᴛɪɴɢ ᴡɪᴛʜ <code>+91</code> ᴏʀ <code>91</code> ғᴏʟʟᴏᴡᴇᴅ ʙʏ 10 ᴅɪɢɪᴛs (e.g., <code>+919876543210</code>).</blockquote></b>", 
            parse_mode=ParseMode.HTML
        )

    # --- 1. Ban & FSUB Check (Silent returns if fail) ---
    banned_users = await db.get_ban_users()
    if user_id in banned_users: return 
    # Pass the message object to not_joined so it can extract the search query for retry logic
    if not await is_subscribed(client, user_id):
        return await not_joined(client, message)

    # --- 2. Credits/Premium/Admin Check ---
    daily_tries, is_premium, _ = await db.get_user_status(user_id)
    is_admin = user_id in ADMINS
    can_search = is_premium or is_admin or daily_tries > 0

    if not can_search:
        return await message.reply_text(
            "<b><blockquote>🛑 ɴᴏ ғʀᴇᴇ ᴛʀɪᴇs ʟᴇғᴛ!\n\n"
            "ʏᴏᴜ ʜᴀᴠᴇ ᴜsᴇᴅ ʏᴏᴜʀ ᴅᴀɪʟʏ ʟɪᴍɪᴛ ᴏғ ғʀᴇᴇ sᴇᴀʀᴄʜᴇs.\n"
            "ᴛᴏ ᴄᴏɴᴛɪɴᴜᴇ sᴇᴀʀᴄʜɪɴɢ, ᴘʟᴇᴀsᴇ ᴄʜᴏᴏsᴇ ᴀɴ ᴏᴘᴛɪᴏɴ:\n"
            "1. ʀᴇғᴇʀ ғʀɪᴇɴᴅs: ɢᴇᴛ +2 ғʀᴇᴇ ᴛʀɪᴇs ғᴏʀ ᴇᴠᴇʀʏ sᴜᴄᴄᴇssғᴜʟ ʀᴇғᴇʀʀᴀʟ. (/referral)\n"
            "2. ʙᴜʏ ᴄʀᴇᴅɪᴛs: ɢᴇᴛ ᴜɴʟɪᴍɪᴛᴇᴅ sᴇᴀʀᴄʜᴇs. (/getplan)</blockquote></b>",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("ɢᴇᴛ ʀᴇғᴇʀʀᴀʟ ʟɪɴᴋ", callback_data="show_referral_info")],
                [InlineKeyboardButton("ʙᴜʏ ᴄʀᴇᴅɪᴛs", callback_data="premium")] 
            ]),
            parse_mode=ParseMode.HTML
        )

    # --- 3. Actual Search Logic and Execution ---
    
    await message.reply_chat_action(ChatAction.TYPING)
    temp_msg = await message.reply(f"<b>🔍 sᴇᴀʀᴄʜɪɴɢ ғᴏʀ <code>{search_query}</code>...</b>", parse_mode=ParseMode.HTML)
    
    search_response = await lookup_number_info(search_query) 
    updated_tries = daily_tries 

    if search_response.get("status") == "success":
        if not is_premium and not is_admin and daily_tries > 0:
            await db.decrement_search_count(user_id)
            updated_tries = daily_tries - 1 
            
        final_message = format_search_results(search_response, is_premium or is_admin)
        
    else:
        final_message = f"❌ sᴇᴀʀᴄʜ ғᴀɪʟᴇᴅ!\n\nʀᴇᴀsᴏɴ: {search_response.get('message', 'ᴜɴᴋɴᴏᴡɴ ᴇʀʀᴏʀ.')}"
    
    new_tries_left = 'ᴜɴʟɪᴍɪᴛᴇᴅ' if is_premium or is_admin else updated_tries
    final_message += f"\n\n— — — — — — — — — — — —\n"
    final_message += f"ᴛʀɪᴇs ʀᴇᴍᴀɪɴɪɴɢ: {new_tries_left}"
    
    try:
        await temp_msg.edit_text(f"<b><blockquote>{final_message}</blockquote></b>", parse_mode=ParseMode.HTML)
    except Exception as e:
        # Use logging in a real environment
        print(f"Error editing search result message: {e}")
        await temp_msg.edit_text(
             f"<b><blockquote>❌ sᴇᴀʀᴄʜ ᴄᴏᴍᴘʟᴇᴛᴇᴅ ʙᴜᴛ ᴅɪsᴘʟᴀʏ ғᴀɪʟᴇᴅ.</b>\n"
             f"ᴛʀɪᴇs ʀᴇᴍᴀɪɴɪɴɢ: {new_tries_left}\n\n"
             f"ᴇʀʀᴏʀ: ᴄᴏᴜʟᴅ ɴᴏᴛ ʀᴇɴᴅᴇʀ sᴇᴀʀᴄʜ ʀᴇsᴜʟᴛs.</blockquote></b>",
             parse_mode=ParseMode.HTML
        )


# =====================================================================================
# PREMIUM & CALLBACK HANDLERS (for buttons in this file)
# =====================================================================================

@Bot.on_callback_query(filters.regex("premium"))
async def handle_premium_callback(client: Client, callback: CallbackQuery):
    """Handles the 'Buy Credits' button from the zero-credit message or /start menu."""
    await callback.answer("ᴄʜᴇᴄᴋɪɴɢ ᴘʟᴀɴs...", show_alert=False)
    # Assumes show_premium_plans handles its own message edit/reply
    await show_premium_plans(client, callback.from_user.id, callback=callback)


@Bot.on_callback_query(filters.regex("show_referral_info"))
async def handle_referral_info_callback(client: Client, callback: CallbackQuery):
    """Handles the 'Referral' button from the zero-credit message or /start menu."""
    await callback.answer("sʜᴏᴡɪɴɢ ʀᴇғᴇʀʀᴀʟ ɪɴғᴏ...", show_alert=False)
    # The referral info function will automatically edit the message/reply
    await send_referral_info(client, callback.from_user.id, callback=callback)


@Bot.on_message(filters.command('referral') & filters.private)
async def referral_command(client: Client, message: Message):
    """Handles the /referral command."""
    await send_referral_info(client, message.from_user.id, message=message)

@Bot.on_message(filters.command('credits') & filters.private)
async def credits_command(client: Client, message: Message):
    """Handles the /credits command (showing user status)."""
    await send_plan_and_credits_info(message.from_user.id, message=message)


@Bot.on_callback_query(filters.regex("^fsub_page_(\d+)$"))
async def fsub_pagination_handler(client: Client, callback: CallbackQuery):
    """Handles pagination for Force Subscribe channels."""
    page = int(callback.matches[0].group(1))
    user_id = callback.from_user.id
    
    # Check subscription again before proceeding to the next page
    if await is_subscribed(client, user_id):
        # User subscribed while navigating pages, delete the FSUB message and show start
        await callback.message.delete()
        # Optionally, manually call the welcome message logic here if you want to avoid a full /start command flow
        return await callback.answer("✅ sᴜʙsᴄʀɪᴘᴛɪᴏɴ ᴄᴏᴍᴘʟᴇᴛᴇᴅ!", show_alert=True)
        
    await callback.answer("ʟᴏᴀᴅɪɴɢ ᴄʜᴀɴɴᴇʟs...", show_alert=False)
    
    # Get all channels again
    all_channels = await db.show_channels()
    
    if not all_channels:
        return await callback.message.edit_text(
            "<b><blockquote>⚠️ ɴᴏ ғᴏʀᴄᴇ sᴜʙsᴄʀɪᴘᴛɪᴏɴ ᴄʜᴀɴɴᴇʟs ғᴏᴜɴᴅ.</blockquote></b>",
            parse_mode=ParseMode.HTML
        )
        
    # Generate the new set of buttons for the requested page
    new_keyboard = await get_fsub_buttons(client, user_id, all_channels, page)
    
    try:
        await callback.message.edit_reply_markup(new_keyboard)
    except FloodWait as e:
        await asyncio.sleep(e.value)
        await callback.message.edit_reply_markup(new_keyboard)
    except Exception as e:
        print(f"Error editing FSUB pagination message: {e}")
        await callback.answer("⚠️ ᴇʀʀᴏʀ ʟᴏᴀᴅɪɴɢ ᴘᴀɢᴇ.", show_alert=True)


# --- FSUB Handler (Refactored for robustness and pagination) ---

async def not_joined(client: Client, message: Message):
    """
    Handles the Force Subscription requirement, now supporting channel pagination.
    """
    user_id = message.from_user.id
    all_channels = await db.show_channels()
    
    # If no channels are configured, let the user proceed
    if not all_channels:
        return 

    # --- 1. Generate the initial message content ---
    fsub_caption_text = FORCE_MSG.format(
        first=message.from_user.first_name,
        last=message.from_user.last_name,
        username=None if not message.from_user.username else '@' + message.from_user.username,
        mention=message.from_user.mention,
        id=message.from_user.id
    )
    final_caption = f"<b><blockquote>{fsub_caption_text}</blockquote></b>"

    # --- 2. Generate buttons for the first page (page 0) ---
    # We pass the message object to get_fsub_buttons for the retry logic 
    buttons = await get_fsub_buttons(client, user_id, all_channels, page=0)
    
    # --- 3. Send the final message ---
    try:
        await message.reply_photo(
            photo=FORCE_PIC,
            caption=final_caption, 
            reply_markup=buttons,
            parse_mode=ParseMode.HTML
        )
    except Exception as e:
        # Fallback to text if photo fails or bot doesn't have permission
        print(f"FSUB photo reply failed: {e}. Falling back to text.")
        await message.reply_text(
            caption=final_caption, 
            reply_markup=buttons,
            parse_mode=ParseMode.HTML
        )
