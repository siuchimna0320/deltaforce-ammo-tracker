#!/usr/bin/env python3
import pandas as pd
from sqlalchemy import create_engine
import os

CSV_PATH = "ammo_prices_wide.csv"

# Read database connection info from environment variables (injected by GitHub Secrets)
DB_HOST = os.environ.get("PGHOST")
DB_PORT = os.environ.get("PGPORT", "5432")
DB_NAME = os.environ.get("PGDATABASE")
DB_USER = os.environ.get("PGUSER")
DB_PASSWORD = os.environ.get("PGPASSWORD")

# Check all required variables exist
if not all([DB_HOST, DB_NAME, DB_USER, DB_PASSWORD]):
    print("Missing database environment variables")
    exit(1)

if not os.path.exists(CSV_PATH):
    print("CSV not found, exit.")
    exit(1)

# Read wide CSV
df_wide = pd.read_csv(CSV_PATH)

# Melt to long format
df_long = df_wide.melt(id_vars=['timestamp'], var_name='ammo_name', value_name='price')
df_long = df_long.dropna(subset=['price'])

# Convert timestamp string to datetime object for proper PostgreSQL storage
df_long['timestamp'] = pd.to_datetime(df_long['timestamp'], format='%Y-%m-%d %H:%M')

# Create PostgreSQL connection
engine = create_engine(f'postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}')

# Write to database (replace table if exists)
df_long.to_sql('ammo_prices', engine, if_exists='replace', index=False)

print(f"Database updated with {len(df_long)} records")
