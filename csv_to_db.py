#!/usr/bin/env python3
import os
import psycopg2

DB_HOST = os.environ.get("PGHOST")
DB_PORT = os.environ.get("PGPORT", "5432")
DB_NAME = os.environ.get("PGDATABASE")
DB_USER = os.environ.get("PGUSER")
DB_PASSWORD = os.environ.get("PGPASSWORD")

print(f"Host: '{DB_HOST}', Port: '{DB_PORT}', DB: '{DB_NAME}', User: '{DB_USER}'")

if not all([DB_HOST, DB_NAME, DB_USER, DB_PASSWORD]):
    print("Missing environment variables")
    exit(1)

try:
    conn = psycopg2.connect(
        host=DB_HOST,
        port=DB_PORT,
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD,
        connect_timeout=5
    )
    conn.close()
    print("Connection successful!")
except Exception as e:
    print(f"Connection failed: {e}")
    exit(1)
