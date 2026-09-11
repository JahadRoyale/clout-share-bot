import sys
import json
import time
import random
import re
import requests
from urllib.parse import quote
from bs4 import BeautifulSoup

def send_facebook_share(cookie_str, target_url):
    """
    Executes a Facebook share using mbasic form extraction and cookie auth.
    """
    try:
        session = requests.Session()
        
        # Parse cookie string into dictionary
        cookies = {}
        for item in cookie_str.split(';'):
            if '=' in item:
                k, v = item.strip().split('=', 1)
                cookies[k] = v.strip()
        
        session.cookies.update(cookies)
        session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8'
        })

        # URL-encode target_url so query params like &fbid= and &set= aren't stripped by mbasic
        encoded_target = quote(target_url, safe='')

        # 1. Request mbasic composer for target link
        composer_url = f"https://mbasic.facebook.com/composer/mbasic/?c_src=share&referrer=permalink&target={encoded_target}"
        res = session.get(composer_url, timeout=12)
        
        if res.status_code != 200:
            print(f"[!] HTTP {res.status_code} while reaching share composer.")
            return False

        soup = BeautifulSoup(res.text, 'html.parser')
        form = soup.find('form', action=re.compile(r'/composer/mbasic/'))
        
        # Fallback check for alternate mbasic form structures
        if not form:
            form = soup.find('form', action=re.compile(r'sharer')) or soup.find('form', action=re.compile(r'/a/mbasic/'))

        if not form:
            page_title = soup.title.string.strip() if soup.title and soup.title.string else 'Unknown Page'
            print(f"[!] Share form not found. Page title returned: '{page_title}'. Cookie may be invalid or blocked.")
            return False

        action = form['action']
        action_url = action if action.startswith('http') else "https://mbasic.facebook.com" + action
        
        # Extract required form inputs (fb_dtsg, jazoest, etc.)
        payload = {}
        for inp in form.find_all('input'):
            name = inp.get('name')
            value = inp.get('value', '')
            if name:
                payload[name] = value

        # 2. Submit the Share Request
        post_res = session.post(action_url, data=payload, timeout=12)
        
        if post_res.status_code == 200:
            return True
            
        return False
    except Exception as e:
        print(f"[!] Share execution error: {e}")
        return False

def main():
    if len(sys.argv) < 2:
        sys.exit(1)

    try:
        payload = json.loads(sys.argv[1])
    except Exception as e:
        print(f"Invalid JSON payload: {e}")
        sys.exit(1)

    target_url = payload.get('link')
    shares_per_bot = payload.get('shares_per_bot', 10)
    bots = payload.get('bots', [])

    print(f"--- [TASK STARTED] Target: {target_url} | Bots: {len(bots)} ---")

    for bot in bots:
        bot_id = bot.get('id')
        cookie_data = bot.get('cookie_data')
        print(f"[*] Processing Bot Account ID: {bot_id}")

        for i in range(shares_per_bot):
            success = send_facebook_share(cookie_data, target_url)
            if not success:
                print(f"[!] Bot {bot_id} failed share submission. Skipping account.")
                break
            
            print(f"[+] Bot {bot_id}: Share {i + 1}/{shares_per_bot} completed.")
            time.sleep(random.randint(4, 8))

        time.sleep(random.randint(5, 10))

    print("--- [TASK COMPLETED] ---")

if __name__ == "__main__":
    main()
