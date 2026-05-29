#!/usr/bin/env python3
import pandas as pd
import sqlite3
import os

CSV_PATH = "ammo_prices_wide.csv"
DB_PATH = "ammo_data.db"

if not os.path.exists(CSV_PATH):
    print("CSV not found, exit.")
    exit()

df_wide = pd.read_csv(CSV_PATH)
df_long = df_wide.melt(id_vars=['timestamp'], var_name='ammo_name', value_name='price')
df_long = df_long.dropna(subset=['price'])
df_long['timestamp'] = pd.to_datetime(df_long['timestamp']).dt.strftime('%Y-%m-%d %H:%M')

conn = sqlite3.connect(DB_PATH)
df_long.to_sql('ammo_prices', conn, if_exists='replace', index=False)
conn.close()

print(f"Database updated with {len(df_long)} records")
