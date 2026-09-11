import sys
import json
import time
import random
import re
import requests

def extract_business_token(cookie_str):
    """
    Bypasses datacenter IP blocks by extracting the EAAG token 
    via Facebook Business Manager instead of mbasic.
    """
    headers = {
        'Cookie': cookie_str,
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }
    try:
        res = requests.get('https://business.facebook.com/business_locations', headers=headers, timeout=15)
        token_match = re.search(r'(EAAG\w+)', res.text)
        if token_match:
            return token_match.group(1)
        return None
    except Exception as e:
        print(f"[!] Token extraction error: {e}")
        return None

def extract_post_id(url):
    """Extracts the numeric ID from the provided link."""
    match = re.search(r'(\d{10,})', url)
    return match.group(1) if match else url

def send_ghost_share(token, post_id):
    """
    Uses the Graph API with published=0. 
    This buffs the share counter without posting visibly to the bot's feed.
    """
    try:
        url = "https://graph.facebook.com/me/feed"
        payload = {
            'link': f"https://m.facebook.com/{post_id}",
            'published': '0',
            'access_token': token
        }
        res = requests.post(url, data=payload, timeout=12)
        data = res.json()

        if res.status_code == 200 and 'id' in data:
            return True, data['id']
        else:
            err_code = data.get('error', {}).get('code', 'N/A')
            error_msg = data.get('error', {}).get('message', res.text)
            return False, f"Code {err_code}: {error_msg}"
    except Exception as e:
        return False, str(e)

def main():
    if len(sys.argv) < 2:
        sys.exit(1)

    try:
        payload = json.loads(sys.argv[1])
    except Exception as e:
        print(f"Invalid JSON payload: {e}")
        sys.exit(1)

    raw_url = payload.get('link')
    target_id = extract_post_id(raw_url)
    shares_per_bot = payload.get('shares_per_bot', 10)
    bots = payload.get('bots', [])

    print(f"--- [TASK STARTED] Target ID: {target_id} | Bots: {len(bots)} ---")

    for bot in bots:
        bot_id = bot.get('id')
        raw_cookie_data = bot.get('cookie_data', '')
        print(f"[*] Processing Bot Account ID: {bot_id}")

        # 1. Generate fresh token on Render using the cookie
        token = extract_business_token(raw_cookie_data)

        if not token:
            print(f"[!] Could not extract EAAG token for Bot {bot_id}. Cookie might be dead.")
            continue
            
        print(f"[+] Successfully extracted Business Token for Bot {bot_id}.")

        # 2. Execute the Ghost Shares
        for i in range(shares_per_bot):
            success, result_msg = send_ghost_share(token, target_id)
            if not success:
                print(f"[!] Bot {bot_id} share failed. {result_msg}")
                break
            
            print(f"[+] Bot {bot_id}: Share {i + 1}/{shares_per_bot} completed (Ghost ID: {result_msg})")
            time.sleep(random.randint(4, 8))

    print("--- [TASK COMPLETED] ---")

if __name__ == "__main__":
    main()
