import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()

conn = psycopg2.connect(
    host=os.getenv('PGHOST'),
    database=os.getenv('PGDATABASE'),
    user=os.getenv('PGUSER'),
    password=os.getenv('PGPASSWORD'),
    port=os.getenv('PGPORT', '5432')
)

cur = conn.cursor()
cur.execute("""
    SELECT column_name 
    FROM information_schema.columns 
    WHERE table_name = 'raw_tweets' 
    ORDER BY ordinal_position
""")

print("Columns in raw_tweets:")
for row in cur.fetchall():
    print(f"  - {row[0]}")

cur.close()
conn.close()