import requests
import pandas as pd
import os
import time
import random
import re
from datetime import datetime, timezone, timedelta
from bs4 import BeautifulSoup

# ========== 配置 ==========
URL = "https://deltaforcetools.gg/auction-house/ammo"
FILE_PATH = "ammo_prices_wide.csv"
REQUEST_TIMEOUT = 30
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36"
]
MIN_DELAY = 1.0
MAX_DELAY = 2.5


def clean_price(price_str: str):
    """从价格字符串中提取数字，返回 float 或 None"""
    cleaned = re.sub(r'[^\d\.\-]', '', price_str.replace(',', ''))
    if cleaned.count('.') > 1:
        parts = cleaned.split('.')
        cleaned = ''.join(parts[:-1]) + '.' + parts[-1]
    try:
        return float(cleaned)
    except ValueError:
        return None


def get_hk_timestamp():
    """返回香港时间字符串，格式：YYYY-MM-DD HH:MM"""
    # UTC+8 没有夏令时，直接加8小时
    hk_time = datetime.utcnow() + timedelta(hours=8)
    return hk_time.strftime("%Y-%m-%d %H:%M")


def scrape_ammo_prices():
    timestamp = get_hk_timestamp()   # 改用香港时间
    data_dict = {"timestamp": timestamp}

    headers = {
        "User-Agent": random.choice(USER_AGENTS),
        "Accept-Language": "en-US,en;q=0.9",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8"
    }

    session = requests.Session()
    try:
        print(f"⏳ [{timestamp}] 抓取中...")
        time.sleep(random.uniform(MIN_DELAY, MAX_DELAY))

        response = session.get(URL, headers=headers, timeout=REQUEST_TIMEOUT)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, 'html.parser')

        table = soup.find("table")
        if not table:
            table = soup.find("table", class_=re.compile(r"(auction|ammo|data)"))
        if not table:
            print("❌ 未找到表格")
            return False

        rows = table.find_all("tr")
        count = 0
        for row in rows:
            cols = row.find_all("td")
            if len(cols) >= 3:
                item_name = cols[1].get_text(strip=True)
                price_text = cols[2].get_text(strip=True)
                if not item_name:
                    continue
                price = clean_price(price_text)
                if price is not None and price > 0:
                    data_dict[item_name] = price
                    count += 1

        if count == 0:
            print("⚠️ 未抓到任何价格")
            return False

        print(f"✅ 抓到 {count} 种子弹")

        new_row = pd.DataFrame([data_dict])

        if os.path.exists(FILE_PATH):
            df = pd.read_csv(FILE_PATH)
            if timestamp in df['timestamp'].values:
                df = df.set_index('timestamp')
                new_row = new_row.set_index('timestamp')
                df.update(new_row)
                df = df.reset_index()
            else:
                df = pd.concat([df, new_row], ignore_index=True)
        else:
            df = new_row

        df = df.sort_values(by="timestamp").reset_index(drop=True)
        df.to_csv(FILE_PATH, index=False, encoding="utf-8")
        print(f"✅ 保存成功，当前共 {len(df)} 条记录")
        return True

    except Exception as e:
        print(f"❌ 错误: {e}")
        return False
    finally:
        session.close()


if __name__ == "__main__":
    scrape_ammo_prices()
