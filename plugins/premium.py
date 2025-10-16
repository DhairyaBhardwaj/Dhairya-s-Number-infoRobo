import os
import json
from pyrogram import Client, filters
from pyrogram.enums import ParseMode
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from bot import Bot 

# --- CONFIGURATION ---
ADMIN_USERNAME = os.environ.get("ADMIN_USERNAME", "Connect_SayXSee_Bot")
FALLBACK_SUPPORT_BOT = os.environ.get("SUPPORT_BOT_LINK", "https://t.me/Connect_SayXSee_Bot")
# ---

# Define the plans: Price (in Rupees), Credits, Display Name
PLANS = {
    "plan_100": {"price": 100, "credits": 30, "name": "BASIC PACK"},
    "plan_200": {"price": 200, "credits": 75, "name": "POWER PACK"},
    "plan_350": {"price": 350, "credits": 150, "name": "PRO PLAN"},
    "plan_600": {"price": 600, "credits": 300, "name": "BULK CREDITS"},
}

# --- Core Logic Functions ---

async def _get_payment_keyboard(price: int, plan_key: str) -> InlineKeyboardMarkup:
    """Helper to create the payment specific keyboard."""
    return InlineKeyboardMarkup(
        [
            # Link to admin's Telegram profile for private transaction
            [InlineKeyboardButton(f"🔒 CONTACT ADMIN FOR PAYMENT ({price} ₹)", url=f"https://t.me/{ADMIN_USERNAME}")],
            # Support link
            [InlineKeyboardButton("TROUBLESHOOTING/SUPPORT", url=FALLBACK_SUPPORT_BOT)],
            # Back button using the fixed callback data
            [InlineKeyboardButton("← BACK TO PLANS", callback_data="show_plans_menu")], 
        ]
    )



# 1. Handler for /getplan command
@Bot.on_message(filters.command("getplan") & filters.private)
async def getplan_command_handler(client: Client, message: Message):
    """Handles the /getplan command."""
    await show_premium_plans(client, message.from_user.id, message=message)

# ---

@Bot.on_callback_query(filters.regex("^show_plans_menu$"))
async def show_plans_menu_handler(client: Client, callback: CallbackQuery):
    """Handles the '← BACK TO PLANS' button click."""
    # Answer the callback immediately to give feedback
    await callback.answer("Loading premium plans menu...", show_alert=False)
    
    # Delegate to the main display function
    await show_premium_plans(client, callback.from_user.id, callback=callback)

# ---

@Bot.on_callback_query(filters.regex("^select_plan_"))
async def process_plan_selection(client: Client, callback: CallbackQuery):
    """
    Handles plan selection using filters.regex. 
    The callback data starts with 'select_plan_'
    """
    
    # 1. Answer the callback first (prevents the "loading" state on Telegram)
    await callback.answer("PRIVATE PAYMENT INSTRUCTIONS ARE READY...", show_alert=False)

    callback_data = callback.data
    
    try:
        
        plan_key = callback_data.replace("select_plan_", "", 1)
        plan_details = PLANS.get(plan_key)

        if not plan_details:
            
            return await callback.answer("⚠️ INVALID PLAN DATA. Please try again.", show_alert=True)
        
        price = plan_details["price"]
        credits = plan_details["credits"]
        plan_name = plan_details["name"]
        
    except Exception as e:
        print(f"Error processing plan selection: {e}")
        return await callback.answer("⚠️ UNABLE TO LOAD PLAN DETAILS. Please try again.", show_alert=True)


    # 2. Build the message and keyboard
    payment_caption = f"💰 **PAYMENT FOR {plan_name}**\n\n"
    payment_caption += f"CREDITS: **{credits}** | PRICE: **₹{price}**\n\n"
    payment_caption += "— — — — — — — — — — — —\n"
    payment_caption += "🔒 **PRIVATE TRANSACTION FLOW**\n\n"
    payment_caption += "1. Click the **'CONTACT ADMIN'** button below.\n"
    payment_caption += "2. Admin will provide you a **private payment link/QR code**.\n"
    payment_caption += "3. After payment, **IMMEDIATELY SEND THE UNIQUE TRANSACTION ID (TID)** to the admin for verification.\n"
    payment_caption += "4. Once verified, your credits will be added instantly."

    keyboard = await _get_payment_keyboard(price, plan_key)

    # 3. Edit the message
    try:
        await callback.message.edit_text(
            f"<b><blockquote>{payment_caption}</blockquote></b>",
            reply_markup=keyboard,
            parse_mode=ParseMode.HTML,
        )
    except Exception:
        
        await callback.answer("Already showing this plan ✅", show_alert=False)

# ---

@Bot.on_callback_query(filters.regex("^close_menu$"))
async def close_menu_handler(client: Client, callback: CallbackQuery):
    """Handles the '❌ CLOSE MENU' button click."""
    # Answer and delete the message
    await callback.answer("MENU CLOSED.", show_alert=False)
    await callback.message.delete()

# --- DISPLAY FUNCTION (Minor Update) ---

async def show_premium_plans(client: Client, user_id: int, message: Message = None, callback: CallbackQuery = None):
    """Shows the main premium plans menu."""

    target = message or callback.message

    text = "👑 **SAYXSEE PREMIUM ACCESS & CREDITS**\n\n"
    text += "UNLIMITED SEARCHES OR BUY BULK CREDITS. ALL CREDITS HAVE LIFETIME VALIDITY.\n\n"
    text += "— — — — — — — — — — — —"

    buttons = []
    for key, plan in PLANS.items():
        # Using the standard 'select_plan_' prefix
        callback_data = f"select_plan_{key}"
        
        button_text = f"👑 {plan['name']} ({plan['credits']} CREDITS) | ₹{plan['price']}"
        buttons.append([InlineKeyboardButton(button_text, callback_data=callback_data)])

    buttons.append([InlineKeyboardButton("❌ CLOSE MENU", callback_data="close_menu")])

    keyboard = InlineKeyboardMarkup(buttons)
    
    try:
        if callback:
            
            await callback.message.edit_text(
                f"<b><blockquote>{text}</blockquote></b>",
                reply_markup=keyboard,
                parse_mode=ParseMode.HTML,
            )
        else:
            # Reply to the command
            await target.reply_text(
                f"<b><blockquote>{text}</blockquote></b>",
                reply_markup=keyboard,
                parse_mode=ParseMode.HTML,
            )
    except Exception:
        if callback:
            # If the edit fails (e.g., text is identical)
            await callback.answer("Already showing this menu ✅", show_alert=False)

