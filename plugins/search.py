import httpx
import logging
import json
import os 

# --- Configuration for Search API ---
# Replace these with your actual details
MAIN_API_URL = "https://leakosintapi.com/"
MAIN_API_TOKEN = "8422691731:dgMQMYPv" 

logging.basicConfig(level=logging.INFO)

async def lookup_number_info(phone_number: str) -> dict:
    """
    Performs an asynchronous phone number lookup against the external API.
    
    Returns:
        A dictionary: {"status": "success", "data": {...}} or 
        {"status": "error", "message": "..."}
    """
    
    payload = {
        "token": MAIN_API_TOKEN,
        "request": phone_number,
        "lang": "en" # Requesting data in English
    }

    try:
        # Using httpx.AsyncClient for non-blocking network requests
        async with httpx.AsyncClient() as client:
            response = await client.post(
                MAIN_API_URL, 
                json=payload, 
                timeout=20.0 # Increased timeout for potential slow APIs
            )
            
            response.raise_for_status()
            
            # The API returns JSON data directly
            # Return the full response content
            return {"status": "success", "data": response.json()}
            
    except httpx.HTTPStatusError as e:
        # Error from the server (e.g., 401, 500)
        return {"status": "error", "message": f"API responded with status code {e.response.status_code}. Please check the API key or try again."}
        
    except httpx.RequestError as e:
        # Connection/Timeout errors
        return {"status": "error", "message": f"Connection error: Could not reach the search service. Reason: {type(e).__name__}."}
        
    except Exception as e:
        # General errors
        return {"status": "error", "message": f"An unexpected error occurred: {str(e)}."}


def format_search_results(api_response: dict, is_premium: bool) -> str:
    """
    Formats the raw API JSON response into a readable, organized message, 
    excluding sensitive/unwanted fields like 'InfoLeak' and 'free_requests_left'.
    """
    data = api_response.get('data', {})
    
    # 1. Check for API-specific internal errors
    if data.get('error'):
        error_msg = data.get('error', 'ᴜɴᴋɴᴏᴡɴ ᴀᴘɪ ᴇʀʀᴏʀ')
        return f"⚠️ <b>sᴇᴀʀᴄʜ ғᴀɪʟᴇᴅ:</b> {error_msg}"

    # 2. Extract summary stats
    total_db = data.get('NumOfDatabase', 0)
    total_results = data.get('NumOfResults', 0)
    
    if total_results == 0:
        return "😔 <b>ɴᴏ ɪɴғᴏʀᴍᴀᴛɪᴏɴ ғᴏᴜɴᴅ.</b>\n\n<i>ᴛʜɪs ɴᴜᴍʙᴇʀ ɪs ɴᴏᴛ ᴘʀᴇsᴇɴᴛ ɪɴ ᴏᴜʀ ᴅᴀᴛᴀsᴇᴛs.</i>"

    output = f"🔎 <b>sᴜᴍᴍᴀʀʏ:</b> <b>{total_results}</b> ʀᴇsᴜʟᴛs ғᴏᴜɴᴅ ɪɴ <b>{total_db}</b> ᴅᴀᴛᴀʙᴀsᴇs.\n"
    
    # 3. Iterate through the 'List' (databases/sources)
    list_data = data.get('List', {})
    
    for source_name, source_details in list_data.items():
        results_in_source = source_details.get('Data', [])
        source_result_count = source_details.get('NumOfResults', len(results_in_source))
        
        output += f"\n\n— — — — — — — — — — — —\n"
        output += f"📊 <b>sᴏᴜʀᴄᴇ:</b> <code>{source_name}</code> ({source_result_count} ʀᴇᴄᴏʀᴅs)\n"
        output += f"— — — — — — — — — — — —\n"
        
        # Determine the display limit (3 for free users, unlimited for premium)
        display_limit = source_result_count
        if not is_premium and source_result_count > 3: 
            display_limit = 3 
        
        # 4. Iterate through the actual data records
        for i, record in enumerate(results_in_source[:display_limit]):
            
            # --- Extract fields (matching the raw data keys) ---
            full_name = record.get('FullName', 'ɴ/ᴀ')
            father_name = record.get('FatherName', 'ɴ/ᴀ')
            doc_number = record.get('DocNumber', 'ɴ/ᴀ')
            region = record.get('Region', 'ɴ/ᴀ')
            
            # Aggregate addresses for display
            addresses = [
                record.get('Address'), 
                record.get('Address2'), 
                record.get('Address3')
            ]
            # Filter out None or empty addresses
            addresses = [a for a in addresses if a and a.strip()]
            
            # Aggregate phones for display
            phones = [
                record.get('Phone'), 
                record.get('Phone2'), 
                record.get('Phone3'), 
                record.get('Phone4'), 
                record.get('Phone5')
            ]
            # Filter out None or empty phones
            phones = [p for p in phones if p and p.strip()]
            
            output += f"\n[ ʀᴇᴄᴏʀᴅ {i+1} ]\n"
            output += f"👤 <b>ɴᴀᴍᴇ:</b> <code>{full_name}</code>\n"
            output += f"👴 <b>ғᴀᴛʜᴇʀ:</b> <code>{father_name}</code>\n"
            output += f"📄 <b>ᴅᴏᴄ ɴᴏ:</b> <code>{doc_number}</code>\n"
            output += f"🌍 <b>ʀᴇɢɪᴏɴ:</b> <code>{region}</code>\n"
            
            if addresses:
                output += f"🏠 <b>ᴀᴅᴅʀᴇssᴇs:</b>\n"
                for j, addr in enumerate(addresses):
                    output += f"  - <code>{addr}</code>\n"
            
            if phones:
                output += f"📞 <b>ᴏᴛʜᴇʀ ᴘʜᴏɴᴇs:</b> <code>{', '.join(phones)}</code>\n"

        # 5. Check if more results are available but hidden for free users
        if source_result_count > 3 and not is_premium:
            output += f"\n...<i>sʜᴏᴡɪɴɢ ᴛᴏᴘ 3 ᴏғ {source_result_count} ʀᴇᴄᴏʀᴅs. ɢᴏ ᴘʀᴇᴍɪᴜᴍ ғᴏʀ ᴀʟʟ ʀᴇsᴜʟᴛs.</i>"


    return output
