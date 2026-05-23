from datetime import datetime
import pandas as pd
import os
import requests
from bs4 import BeautifulSoup

URL = "https://deltaforcetools.gg/auction-house/ammo"
FILE_PATH = "ammo_prices_wide.csv"

def scrape_ammo_prices():
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
    data_dict = {"timestamp": timestamp}
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36"
    }
    
    try:
        response = requests.get(URL, headers=headers, timeout=30)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        rows = soup.select("table tr")
        count = 0
        
        for row in rows:
            cols = row.find_all("td")
            if len(cols) >= 3:
                item_name = cols[1].get_text(strip=True)
                price_text = cols[2].get_text(strip=True).replace("$", "").replace(",", "").strip()
                
                try:
                    price = float(price_text)
                    if item_name and price > 0:
                        data_dict[item_name] = price
                        count += 1
                except:
                    pass
        
        print(f"找到 {count} 種子彈")
        
        if count == 0:
            print("⚠️ 未能抓到資料")
            return False
        
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
        
        print(f"✅ [{timestamp}] 成功抓取 {count} 種子彈")
        return True
        
    except Exception as e:
        print(f"❌ 錯誤: {e}")
        return False

if __name__ == "__main__":
    scrape_ammo_prices()
