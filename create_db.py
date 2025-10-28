import os
import psycopg2
from psycopg2 import sql
from dotenv import load_dotenv

load_dotenv()

# Connect to default 'postgres' database
conn = psycopg2.connect(
    host=os.getenv('PGHOST', 'localhost'),
    database='postgres',  # Connect to default DB first
    user=os.getenv('PGUSER', 'postgres'),
    password=os.getenv('PGPASSWORD'),
    port=os.getenv('PGPORT', '5432')
)
conn.autocommit = True
cur = conn.cursor()

# Create database
try:
    cur.execute(sql.SQL("CREATE DATABASE {}").format(sql.Identifier("grok_trends")))
    print("✅ Database 'grok_trends' created!")
except psycopg2.errors.DuplicateDatabase:
    print("⚠️ Database 'grok_trends' already exists")
except Exception as e:
    print(f"Error: {e}")

cur.close()
conn.close()