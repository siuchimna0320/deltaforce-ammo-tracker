import requests
import pandas as pd
import os
import time
import random
import re
from datetime import datetime, timedelta
from bs4 import BeautifulSoup

# ========== 配置 ==========
BASE_URL = "https://deltaforcetools.gg/auction-house/ammo"
FILE_PATH = "ammo_prices_wide.csv"
REQUEST_TIMEOUT = 30
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36"
]
MIN_DELAY = 1.0
MAX_DELAY = 2.5
MAX_PAGES_LIMIT = 20   # 安全上限，防止死循环


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
    hk_time = datetime.utcnow() + timedelta(hours=8)
    return hk_time.strftime("%Y-%m-%d %H:%M")


def scrape_single_page(page_num):
    """
    抓取单页数据
    返回: (page_data_dict, is_empty)
        page_data_dict: 弹药名称 -> 价格
        is_empty: True 表示该页确实无数据（表格为空或页面无效），False 表示可能有数据或请求失败
    """
    url = f"{BASE_URL}?page={page_num}" if page_num > 1 else BASE_URL
    print(f"  正在抓取第 {page_num} 页...")

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

        # 定位表格
        table = soup.find("table")
        if not table:
            table = soup.find("table", class_=re.compile(r"(auction|ammo|data)"))
        if not table:
            print(f"    ⚠️ 第 {page_num} 页未找到表格，视为无数据")
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
            print(f"    ⚠️ 第 {page_num} 页表格存在但未解析到任何弹药，视为无数据")
            return {}, True

        print(f"    ✅ 第 {page_num} 页抓取成功，共 {len(page_data)} 种弹药")
        return page_data, False

    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 404:
            print(f"    ⚠️ 第 {page_num} 页返回 404，停止翻页")
        else:
            print(f"    ❌ 第 {page_num} 页 HTTP 错误: {e}")
        return {}, True
    except Exception as e:
        print(f"    ❌ 第 {page_num} 页抓取失败: {e}")
        # 如果是网络临时故障，返回空但 is_empty=False 以便重试？此处简单认为该页无数据并停止
        return {}, True
    finally:
        session.close()


def scrape_ammo_prices():
    timestamp = get_hk_timestamp()
    print(f"⏳ [{timestamp}] 开始动态抓取弹药价格（自动探测最后一页）...")

    all_ammo_data = {}
    page = 1

    while page <= MAX_PAGES_LIMIT:
        page_prices, is_empty = scrape_single_page(page)
        if is_empty:
            print(f"🛑 第 {page} 页无有效数据，停止翻页。")
            break
        all_ammo_data.update(page_prices)
        page += 1

    if page == 1 and not all_ammo_data:
        # 第一页就无数据
        print("⚠️ 所有页面均未抓到任何价格，任务终止")
        return False

    print(f"✅ 总计抓取到 {len(all_ammo_data)} 种弹药，共 {page-1} 页")

    # 构建新数据行
    data_dict = {"timestamp": timestamp}
    data_dict.update(all_ammo_data)
    new_row = pd.DataFrame([data_dict])

    # 更新或追加 CSV 文件
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
    print(f"✅ 数据已保存至 {FILE_PATH}，当前共有 {len(df)} 条记录")
    return True


if __name__ == "__main__":
    scrape_ammo_prices()
