import psycopg2, os
from dotenv import load_dotenv

load_dotenv()
conn = psycopg2.connect(
    host=os.getenv('PGHOST'),
    database=os.getenv('PGDATABASE'),
    user=os.getenv('PGUSER'),
    password=os.getenv('PGPASSWORD'),
    port=os.getenv('PGPORT', '5432')
)
conn.autocommit = True
cur = conn.cursor()

print("Dropping old tables...")
cur.execute('DROP TABLE IF EXISTS trend_agg_hourly CASCADE')
cur.execute('DROP TABLE IF EXISTS trend_aggregations CASCADE')
cur.execute('DROP TABLE IF EXISTS topics CASCADE')
cur.execute('DROP TABLE IF EXISTS raw_tweets CASCADE')
cur.execute('DROP TABLE IF EXISTS api_usage CASCADE')

print("✅ Tables dropped. Now run: python collector/db_init.py")
cur.close()
conn.close()