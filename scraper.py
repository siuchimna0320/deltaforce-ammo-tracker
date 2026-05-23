import requests
import pandas as pd
import os
import time
import random
import re
import sys
from datetime import datetime, timedelta
from bs4 import BeautifulSoup

# ========== CONFIGURATION ==========
BASE_URL = "https://deltaforcetools.gg/auction-house/ammo"   # English version
FILE_PATH = "ammo_prices_wide.csv"
REQUEST_TIMEOUT = 30
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36"
]
MIN_DELAY = 1.0
MAX_DELAY = 2.5
MAX_PAGES_LIMIT = 20          # Safety upper bound


def clean_price(price_str: str):
    """Extract numeric price from string, return float or None"""
    try:
        cleaned = re.sub(r'[^\d\.\-]', '', price_str.replace(',', '').strip())
        if cleaned.count('.') > 1:
            parts = cleaned.split('.')
            cleaned = ''.join(parts[:-1]) + '.' + parts[-1]
        return float(cleaned)
    except:
        return None


def get_hk_timestamp():
    """Return Hong Kong time string format: YYYY-MM-DD HH:MM"""
    hk_time = datetime.utcnow() + timedelta(hours=8)
    return hk_time.strftime("%Y-%m-%d %H:%M")


def scrape_single_page(page_num):
    """
    Scrape a single page.
    Returns (data_dict, is_empty)
    """
    url = f"{BASE_URL}?page={page_num}" if page_num > 1 else BASE_URL
    print(f"  Scraping page {page_num}: {url}")

    headers = {
        "User-Agent": random.choice(USER_AGENTS),
        "Accept-Language": "en-US,en;q=0.9",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8"
    }

    session = requests.Session()
    try:
        time.sleep(random.uniform(MIN_DELAY, MAX_DELAY))
        response = session.get(url, headers=headers, timeout=REQUEST_TIMEOUT)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, 'html.parser')
        table = soup.find("table")
        if not table:
            table = soup.find("table", class_=re.compile(r"(auction|ammo|data)"))
        if not table:
            print(f"    ⚠️ Page {page_num}: table not found -> treat as empty")
            return {}, True

        rows = table.find_all("tr")
        page_data = {}
        for row in rows:
            cols = row.find_all("td")
            if len(cols) >= 3:
                item_name = cols[1].get_text(strip=True)
                price_text = cols[2].get_text(strip=True)
                if not item_name:
                    continue
                price = clean_price(price_text)
                if price is not None and price > 0:
                    page_data[item_name] = price

        if not page_data:
            print(f"    ⚠️ Page {page_num}: table exists but no valid ammo -> empty")
            return {}, True

        print(f"    ✅ Page {page_num}: success, {len(page_data)} ammo types")
        return page_data, False

    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 404:
            print(f"    ⚠️ Page {page_num}: 404 Not Found -> stop")
        else:
            print(f"    ❌ Page {page_num}: HTTP error {e}")
        return {}, True
    except Exception as e:
        print(f"    ❌ Page {page_num}: exception {type(e).__name__}: {e}")
        return {}, True
    finally:
        session.close()


def safe_read_csv(file_path):
    """
    Safely read CSV. Return empty DataFrame if file missing, empty, or corrupted.
    """
    if not os.path.exists(file_path):
        return pd.DataFrame()
    if os.path.getsize(file_path) == 0:
        print(f"⚠️ File {file_path} is empty, will treat as new file")
        return pd.DataFrame()
    try:
        df = pd.read_csv(file_path)
        if df.empty:
            print(f"⚠️ File {file_path} has no data rows, will treat as new file")
            return pd.DataFrame()
        return df
    except pd.errors.EmptyDataError:
        print(f"⚠️ File {file_path} has no columns, will treat as new file")
        return pd.DataFrame()
    except Exception as e:
        print(f"⚠️ Failed to read {file_path}: {e}, will treat as new file")
        return pd.DataFrame()


def scrape_ammo_prices():
    timestamp = get_hk_timestamp()
    print(f"⏳ [{timestamp}] Starting dynamic scraping (English version, auto-detect pages)...")

    all_ammo_data = {}
    page = 1
    consecutive_empty = 0

    while page <= MAX_PAGES_LIMIT:
        page_prices, is_empty = scrape_single_page(page)
        if is_empty:
            consecutive_empty += 1
            if consecutive_empty >= 2:
                print(f"🛑 Stopping after {consecutive_empty} consecutive empty pages.")
                break
        else:
            consecutive_empty = 0
            all_ammo_data.update(page_prices)
        page += 1

    if page == 1 and not all_ammo_data:
        print("⚠️ No ammo prices found on any page. Aborting.")
        return False

    effective_pages = page - 1 - consecutive_empty
    print(f"✅ Total collected: {len(all_ammo_data)} ammo types from {effective_pages} page(s)")

    # Build new row
    data_dict = {"timestamp": timestamp}
    data_dict.update(all_ammo_data)
    new_row = pd.DataFrame([data_dict])

    # Read existing CSV safely
    df = safe_read_csv(FILE_PATH)

    if df.empty:
        df = new_row
    else:
        if timestamp in df['timestamp'].values:
            df = df.set_index('timestamp')
            new_row_indexed = new_row.set_index('timestamp')
            df.update(new_row_indexed)
            df = df.reset_index()
        else:
            df = pd.concat([df, new_row], ignore_index=True)

    df = df.sort_values(by="timestamp").reset_index(drop=True)
    df.to_csv(FILE_PATH, index=False, encoding="utf-8")
    print(f"✅ Data saved to {FILE_PATH}, total {len(df)} records")
    return True


if __name__ == "__main__":
    try:
        success = scrape_ammo_prices()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"❌ Unhandled exception: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
