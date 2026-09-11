import sys
import json
import time
import random
import re
import requests
from urllib.parse import quote
from bs4 import BeautifulSoup

def normalize_facebook_url(url):
    """
    Converts desktop photo viewer URLs, Reels, and complex parameters
    into clean Facebook entity URLs that mbasic composer can process.
    """
    # 1. Extract fbid from desktop photo links
    fbid_match = re.search(r'[?&]fbid=(\d+)', url)
    if fbid_match:
        return f"https://www.facebook.com/{fbid_match.group(1)}"
        
    # 2. Extract story_fbid from post links
    story_match = re.search(r'[?&]story_fbid=(\d+)', url)
    if story_match:
        return f"https://www.facebook.com/{story_match.group(1)}"

    # 3. Clean FB Reel links
    reel_match = re.search(r'reel/(\d+)', url)
    if reel_match:
        return f"https://www.facebook.com/reel/{reel_match.group(1)}/"

    # 4. Extract numeric post IDs from /posts/ or /photos/ paths
    post_match = re.search(r'/(?:posts|permalink|photos)/(\d+)', url)
    if post_match:
        return f"https://www.facebook.com/{post_match.group(1)}"

    return url

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

        # Normalize URL to resolve desktop photo links and query strings
        clean_target = normalize_facebook_url(target_url)
        encoded_target = quote(clean_target, safe='')

        # 1. Request mbasic composer for target link
        composer_url = f"https://mbasic.facebook.com/composer/mbasic/?c_src=share&referrer=permalink&target={encoded_target}"
        res = session.get(composer_url, timeout=12)
        
        if res.status_code != 200:
            print(f"[!] HTTP {res.status_code} while reaching share composer.")
            return False

        soup = BeautifulSoup(res.text, 'html.parser')
        form = soup.find('form', action=re.compile(r'/composer/mbasic/'))
        
        # Fallback selectors if default composer form is missing
        if not form:
            form = soup.find('form', action=re.compile(r'sharer')) or soup.find('form', action=re.compile(r'/a/mbasic/'))

        if not form:
            page_title = soup.title.string.strip() if soup.title and soup.title.string else 'Unknown Page'
            print(f"[!] Share form not found. Page title: '{page_title}'. Target used: {clean_target}")
            return False

        action = form['action']
        action_url = action if action.startswith('http') else "https://mbasic.facebook.com" + action
        
        # Extract required hidden inputs (fb_dtsg, jazoest, etc.)
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

    raw_url = payload.get('link')
    shares_per_bot = payload.get('shares_per_bot', 10)
    bots = payload.get('bots', [])

    print(f"--- [TASK STARTED] Raw Target: {raw_url} | Bots: {len(bots)} ---")

    for bot in bots:
        bot_id = bot.get('id')
        cookie_data = bot.get('cookie_data')
        print(f"[*] Processing Bot Account ID: {bot_id}")

        for i in range(shares_per_bot):
            success = send_facebook_share(cookie_data, raw_url)
            if not success:
                print(f"[!] Bot {bot_id} failed share submission. Skipping account.")
                break
            
            print(f"[+] Bot {bot_id}: Share {i + 1}/{shares_per_bot} completed.")
            time.sleep(random.randint(4, 8))

        time.sleep(random.randint(5, 10))

    print("--- [TASK COMPLETED] ---")

if __name__ == "__main__":
    main()
