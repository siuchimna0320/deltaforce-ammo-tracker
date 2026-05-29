#!/usr/bin/env python3
import pandas as pd
from sqlalchemy import create_engine
import os

CSV_PATH = "ammo_prices_wide.csv"

# 从环境变量读取数据库连接信息
DB_HOST = os.environ.get("PGHOST")
DB_PORT = os.environ.get("PGPORT", "5432")
DB_NAME = os.environ.get("PGDATABASE")
DB_USER = os.environ.get("PGUSER")
DB_PASSWORD = os.environ.get("PGPASSWORD")

# 检查必要变量
if not all([DB_HOST, DB_NAME, DB_USER, DB_PASSWORD]):
    print("Missing database environment variables")
    print(f"PGHOST={DB_HOST}, PGDATABASE={DB_NAME}, PGUSER={DB_USER}")
    exit(1)

if not os.path.exists(CSV_PATH):
    print("CSV not found, exit.")
    exit(1)

df_wide = pd.read_csv(CSV_PATH)
df_long = df_wide.melt(id_vars=['timestamp'], var_name='ammo_name', value_name='price')
df_long = df_long.dropna(subset=['price'])
df_long['timestamp'] = pd.to_datetime(df_long['timestamp'], format='%Y-%m-%d %H:%M')

# 连接数据库
conn_str = f'postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}'
print(f"Connecting to {DB_HOST}:{DB_PORT}")  # 调试输出
engine = create_engine(conn_str)

df_long.to_sql('ammo_prices', engine, if_exists='replace', index=False)
print(f"Database updated with {len(df_long)} records")
