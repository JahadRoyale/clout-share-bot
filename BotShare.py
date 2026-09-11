import sys
import json
import time
import random
import re
import requests

def share_via_graph_api(token, target_url):
    """Publishes a share via Graph API by passing the URL as a status message."""
    try:
        url = "https://graph.facebook.com/v18.0/me/feed"
        # Using 'message' bypasses the strict 'link' parameter validation
        # Facebook will automatically generate the share preview.
        payload = {
            'message': target_url,
            'access_token': token
        }
        res = requests.post(url, data=payload, timeout=12)
        data = res.json()

        if res.status_code == 200 and 'id' in data:
            print(f"[+] Graph API Share Success! Created Post ID: {data['id']}")
            return True
        else:
            err_code = data.get('error', {}).get('code', 'N/A')
            error_msg = data.get('error', {}).get('message', res.text)
            print(f"[!] Graph API Error (Code {err_code}): {error_msg}")
            return False
    except Exception as e:
        print(f"[!] Graph API Exception: {e}")
        return False

def extract_token_from_string(text):
    match = re.search(r'(EAA[A-Za-z0-9]+)', text)
    return match.group(1) if match else None

def main():
    if len(sys.argv) < 2:
        sys.exit(1)

    try:
        payload = json.loads(sys.argv[1])
    except Exception as e:
        print(f"Invalid JSON payload: {e}")
        sys.exit(1)

    # Graph API handles raw pfbid links perfectly natively
    target_url = payload.get('link')
    shares_per_bot = payload.get('shares_per_bot', 10)
    bots = payload.get('bots', [])

    print(f"--- [TASK STARTED] Target: {target_url} | Bots: {len(bots)} ---")

    for bot in bots:
        bot_id = bot.get('id')
        raw_cookie_data = bot.get('cookie_data', '')
        print(f"[*] Processing Bot Account ID: {bot_id}")

        token = extract_token_from_string(raw_cookie_data)

        if not token:
            print(f"[!] No EAAG/EAAB Access Token found for Bot {bot_id}. Please re-import bot with Token included.")
            continue

        for i in range(shares_per_bot):
            success = share_via_graph_api(token, target_url)
            if not success:
                print(f"[!] Bot {bot_id} share failed. Stopping tasks for this account.")
                break
            
            print(f"[+] Bot {bot_id}: Share {i + 1}/{shares_per_bot} completed.")
            time.sleep(random.randint(4, 7))

    print("--- [TASK COMPLETED] ---")

if __name__ == "__main__":
    main()
