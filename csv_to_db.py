#!/usr/bin/env python3
import pandas as pd
import psycopg2
from sqlalchemy import create_engine
import os

CSV_PATH = "ammo_prices_wide.csv"

DB_HOST = os.environ.get("PGHOST")
DB_PORT = os.environ.get("PGPORT", "5432")
DB_NAME = os.environ.get("PGDATABASE")
DB_USER = os.environ.get("PGUSER")
DB_PASSWORD = os.environ.get("PGPASSWORD")

if not all([DB_HOST, DB_NAME, DB_USER, DB_PASSWORD]):
    print("Missing database environment variables")
    exit(1)

if not os.path.exists(CSV_PATH):
    print("CSV not found, exit.")
    exit(1)

df_wide = pd.read_csv(CSV_PATH)
df_long = df_wide.melt(id_vars=['timestamp'], var_name='ammo_name', value_name='price')
df_long = df_long.dropna(subset=['price'])
df_long['timestamp'] = pd.to_datetime(df_long['timestamp'], format='%Y-%m-%d %H:%M')

# 使用 psycopg2 直接连接，绕过 SQLAlchemy URL 解析
conn = psycopg2.connect(
    host=DB_HOST,
    port=DB_PORT,
    dbname=DB_NAME,
    user=DB_USER,
    password=DB_PASSWORD
)

# 使用 SQLAlchemy 的 engine 但用已有的连接
engine = create_engine('postgresql+psycopg2://', creator=lambda: conn)

df_long.to_sql('ammo_prices', engine, if_exists='replace', index=False)
conn.close()
print(f"Database updated with {len(df_long)} records")
