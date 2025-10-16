

import motor, asyncio
import motor.motor_asyncio
import time
import pymongo, os
from config import DB_URI, DB_NAME
from bot import Bot
import logging
from datetime import datetime, timedelta

# Existing synchronous client (used only if needed outside motor context)
dbclient = pymongo.MongoClient(DB_URI)
database = dbclient[DB_NAME]

logging.basicConfig(level=logging.INFO)


class Rohit:

    def __init__(self, DB_URI, DB_NAME):
        self.dbclient = motor.motor_asyncio.AsyncIOMotorClient(DB_URI)
        self.database = self.dbclient[DB_NAME]

        self.channel_data = self.database['channels']
        self.admins_data = self.database['admins']
        self.user_data = self.database['users'] # Stores: _id, daily_searches, is_premium, premium_expiry, referred_by, referral_count
        self.banned_user_data = self.database['banned_user']
        self.autho_user_data = self.database['autho_user']
        self.del_timer_data = self.database['del_timer']
        self.fsub_data = self.database['fsub']   
        self.rqst_fsub_data = self.database['request_forcesub']
        self.rqst_fsub_Channel_data = self.database['request_forcesub_channel']
        
        # NEW: Redeem Code Collection for promotional codes
        self.redeem_codes = self.database['redeem_codes']


    # =====================================================================================
    # USER DATA & CREDIT MANAGEMENT
    # =====================================================================================

    async def add_user_with_referrer(self, user_id: int, referrer_id: int = None):
        """Adds a new user with default credits and referrer ID."""
        user_doc = {
            '_id': user_id,
            'daily_searches': 2,                        # Default 2 free tries
            'is_premium': False,                        # Default non-premium
            'premium_expiry': None,                     # No expiry date initially
            'referred_by': referrer_id,                 # ID of the user who referred them
            'referral_count': 0,                        # Count of users this user has referred
            'last_search_date': datetime.min            # To track daily reset boundary (optional)
        }
        await self.user_data.insert_one(user_doc)
        return

    async def present_user(self, user_id: int):
        found = await self.user_data.find_one({'_id': user_id})
        return bool(found)

    async def add_user(self, user_id: int):
        """Adds an existing user without referral info (fallback for older code/simple add)."""
        if not await self.present_user(user_id):
            await self.add_user_with_referrer(user_id)
        return
        
    async def get_user_status(self, user_id: int) -> tuple[int, bool, bool]:
        """Returns (daily_searches, is_premium, is_banned) status of the user.
           Also handles checking if daily reset is needed."""
        
        user = await self.user_data.find_one({'_id': user_id})
        banned = await self.ban_user_exist(user_id)

        is_premium = user.get('is_premium', False) if user else False
        daily_tries = user.get('daily_searches', 0) if user else 0
        last_search_date = user.get('last_search_date', datetime.min) if user else datetime.min

        # Implement premium expiry check
        if is_premium and user.get('premium_expiry') and user['premium_expiry'] < datetime.now():
            await self.user_data.update_one({'_id': user_id}, {'$set': {'is_premium': False, 'premium_expiry': None}})
            is_premium = False
            
        # Implement DAILY FREE CREDIT RESET (Set to 2 if 24 hours passed AND not premium)
        if not is_premium:
            if datetime.now() >= last_search_date + timedelta(hours=24):
                # Only reset if the user's current searches are less than the base daily allowance (2)
                # This ensures referral/redeem credits are not wiped out, only the daily allowance is restored
                if daily_tries < 2: 
                    await self.user_data.update_one({'_id': user_id}, {'$set': {'daily_searches': 2, 'last_search_date': datetime.now()}})
                    daily_tries = 2
                
        return (daily_tries, is_premium, banned)

    async def decrement_search_count(self, user_id: int):
        """Decrements the user's daily search count by 1 and updates the last_search_date."""
        await self.user_data.update_one(
            {'_id': user_id, 'daily_searches': {'$gt': 0}},
            {
                '$inc': {'daily_searches': -1},
                '$set': {'last_search_date': datetime.now()} # Update timestamp on every search
            }
        )

    async def add_referral_credits(self, user_id: int, count: int = 2):
        """Increments the user's search count (used for successful referrals AND redeem codes)."""
        await self.user_data.update_one(
            {'_id': user_id},
            {'$inc': {'daily_searches': count}},
            upsert=True
        )
        
    async def update_referral_count(self, user_id: int, increment: int = 1):
        """Increments the count of successful referrals by this user."""
        await self.user_data.update_one(
            {'_id': user_id},
            {'$inc': {'referral_count': increment}},
            upsert=True
        )

    async def get_referral_count(self, user_id: int) -> int:
        """Gets the total number of successful referrals by the user."""
        user = await self.user_data.find_one({'_id': user_id})
        return user.get('referral_count', 0) if user else 0

    async def get_premium_expiry(self, user_id: int) -> datetime or None:
        """Gets the premium expiration date."""
        user = await self.user_data.find_one({'_id': user_id})
        return user.get('premium_expiry') if user else None

    # =====================================================================================
    # NEW: REDEEM CODE MANAGEMENT
    # =====================================================================================

    async def add_redeem_code(self, code: str, data: dict) -> bool:
        """Adds a new redeem code document."""
        try:
            # Use the code itself as the primary key (_id) for easy retrieval
            data['_id'] = code 
            await self.redeem_codes.insert_one(data)
            return True
        except Exception as e:
            logging.error(f"Error adding redeem code {code}: {e}")
            return False

    async def get_redeem_code(self, code: str) -> dict or None:
        """Retrieves a redeem code document by its ID."""
        try:
            return await self.redeem_codes.find_one({'_id': code})
        except Exception as e:
            logging.error(f"Error getting redeem code {code}: {e}")
            return None

    async def update_redeem_code(self, code: str, update_data: dict) -> bool:
        """Updates a redeem code document."""
        try:
            await self.redeem_codes.update_one(
                {'_id': code},
                {'$set': update_data}
            )
            return True
        except Exception as e:
            logging.error(f"Error updating redeem code {code}: {e}")
            return False

    # --- End of NEW Credit Management ---

    async def full_userbase(self):
        user_docs = await self.user_data.find().to_list(length=None)
        user_ids = [doc['_id'] for doc in user_docs]
        return user_ids

    async def del_user(self, user_id: int):
        await self.user_data.delete_one({'_id': user_id})
        return


    # ADMIN DATA (RETAINED)
    async def admin_exist(self, admin_id: int):
        found = await self.admins_data.find_one({'_id': admin_id})
        return bool(found)
    # ... (rest of admin functions)
    async def add_admin(self, admin_id: int):
        if not await self.admin_exist(admin_id):
            await self.admins_data.insert_one({'_id': admin_id})
            return

    async def del_admin(self, admin_id: int):
        if await self.admin_exist(admin_id):
            await self.admins_data.delete_one({'_id': admin_id})
            return

    async def get_all_admins(self):
        users_docs = await self.admins_data.find().to_list(length=None)
        user_ids = [doc['_id'] for doc in users_docs]
        return user_ids


    # BAN USER DATA (RETAINED)
    async def ban_user_exist(self, user_id: int):
        found = await self.banned_user_data.find_one({'_id': user_id})
        return bool(found)
    # ... (rest of ban user functions)
    async def add_ban_user(self, user_id: int):
        if not await self.ban_user_exist(user_id):
            await self.banned_user_data.insert_one({'_id': user_id})
            return

    async def del_ban_user(self, user_id: int):
        if await self.ban_user_exist(user_id):
            await self.banned_user_data.delete_one({'_id': user_id})
            return

    async def get_ban_users(self):
        users_docs = await self.banned_user_data.find().to_list(length=None)
        user_ids = [doc['_id'] for doc in users_docs]
        return user_ids


    # AUTO DELETE TIMER SETTINGS (RETAINED but irrelevant for this bot)
    # RETAINED: `get_del_timer` is called in start.py, so keeping this for now.
    async def set_del_timer(self, value: int):        
        existing = await self.del_timer_data.find_one({})
        if existing:
            await self.del_timer_data.update_one({}, {'$set': {'value': value}})
        else:
            await self.del_timer_data.insert_one({'value': value})

    async def get_del_timer(self):
        data = await self.del_timer_data.find_one({})
        # Changed default value to 0 as auto-delete is removed from start.py
        if data:
            return data.get('value', 0) 
        return 0


    # CHANNEL MANAGEMENT (RETAINED)
    async def channel_exist(self, channel_id: int):
        found = await self.fsub_data.find_one({'_id': channel_id})
        return bool(found)
    # ... (rest of channel functions)
    async def add_channel(self, channel_id: int):
        if not await self.channel_exist(channel_id):
            await self.fsub_data.insert_one({'_id': channel_id})
            return

    async def rem_channel(self, channel_id: int):
        if await self.channel_exist(channel_id):
            await self.fsub_data.delete_one({'_id': channel_id})
            return

    async def show_channels(self):
        channel_docs = await self.fsub_data.find().to_list(length=None)
        channel_ids = [doc['_id'] for doc in channel_docs]
        return channel_ids

    
    async def get_channel_mode(self, channel_id: int):
        data = await self.fsub_data.find_one({'_id': channel_id})
        return data.get("mode", "off") if data else "off"

    async def set_channel_mode(self, channel_id: int, mode: str):
        await self.fsub_data.update_one(
            {'_id': channel_id},
            {'$set': {'mode': mode}},
            upsert=True
        )

    # REQUEST FORCE-SUB MANAGEMENT (RETAINED)

    async def req_user(self, channel_id: int, user_id: int):
        try:
            await self.rqst_fsub_Channel_data.update_one(
                {'_id': int(channel_id)},
                {'$addToSet': {'user_ids': int(user_id)}},
                upsert=True
            )
        except Exception as e:
            print(f"[DB ERROR] Failed to add user to request list: {e}")

    async def del_req_user(self, channel_id: int, user_id: int):
        await self.rqst_fsub_Channel_data.update_one(
            {'_id': channel_id}, 
            {'$pull': {'user_ids': user_id}}
        )

    async def req_user_exist(self, channel_id: int, user_id: int):
        try:
            found = await self.rqst_fsub_Channel_data.find_one({
                '_id': int(channel_id),
                'user_ids': int(user_id)
            })
            return bool(found)
        except Exception as e:
            print(f"[DB ERROR] Failed to check request list: {e}")
            return False  

    async def reqChannel_exist(self, channel_id: int):
        channel_ids = await self.show_channels()
        if channel_id in channel_ids:
            return True
        else:
            return False


db = Rohit(DB_URI, DB_NAME)
