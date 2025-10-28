import os
import psycopg2
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

# Create interest signups table
cur.execute("""
    CREATE TABLE IF NOT EXISTS interest_signups (
        id SERIAL PRIMARY KEY,
        email VARCHAR(255) UNIQUE NOT NULL,
        created_at TIMESTAMP DEFAULT NOW(),
        referrer VARCHAR(100),
        user_agent TEXT
    )
""")

conn.commit()
cur.close()
conn.close()

print("✅ Interest signups table created!")