#!/usr/bin/env python3
import pandas as pd
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

# 确保使用 postgresql+psycopg2 协议，并显式指定 host 和 port
engine = create_engine(f'postgresql+psycopg2://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}')

df_long.to_sql('ammo_prices', engine, if_exists='replace', index=False)
print(f"Database updated with {len(df_long)} records")
