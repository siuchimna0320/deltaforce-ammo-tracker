from datetime import datetime
import pandas as pd
import os
import time
from playwright.sync_api import sync_playwright

URL = "https://deltaforcetools.gg/auction-house/ammo"
FILE_PATH = "ammo_prices_wide.csv"

def scrape_ammo_prices():
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
    data_dict = {"timestamp": timestamp}
    
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            page.set_extra_http_headers({
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36"
            })
            
            print(f"正在訪問網站... [{timestamp}]")
            page.goto(URL, wait_until="networkidle", timeout=60000)
            
            # 等待表格載入
            page.wait_for_selector("table", timeout=30000)
            time.sleep(4)   # 給網站時間載入資料
            
            rows = page.locator("table tr").all()
            count = 0
            
            for row in rows:
                cols = row.locator("td").all()
                if len(cols) >= 3:
                    item_name = cols[1].inner_text().strip()
                    price_text = cols[2].inner_text().strip().replace("$", "").replace(",", "").strip()
                    
                    try:
                        price = float(price_text)
                        if item_name and price > 0:
                            data_dict[item_name] = price
                            count += 1
                    except:
                        pass
            
            browser.close()
        
        if count == 0:
            print("⚠️ 未能抓到價格資料")
            return False
        
        # 儲存為寬格式 CSV
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
        
        print(f"✅ [{timestamp}] 成功抓取 {count} 種子彈 Current Price")
        return True
        
    except Exception as e:
        print(f"❌ 抓取失敗: {e}")
        return False

if __name__ == "__main__":
    scrape_ammo_prices()
