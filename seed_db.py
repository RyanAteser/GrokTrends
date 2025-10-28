# seed_db.py
import os, sys
import psycopg
from psycopg.rows import tuple_row

SCHEMA_SQL = r"""
-- put the same SQL from schema.sql here (tables + optional seed)
-- or: keep it in schema.sql and read it from disk (see below)
"""

def run_sql(conn, sql):
    with conn.cursor() as cur:
        cur.execute(sql)
    conn.commit()

def main():
    dsn = os.getenv("DATABASE_URL")
    if not dsn:
        print("DATABASE_URL not set", file=sys.stderr)
        sys.exit(1)

    # safer default in cloud
    if "sslmode" not in dsn:
        dsn += ("&" if "?" in dsn else "?") + "sslmode=require"

    schema_path = os.getenv("SCHEMA_PATH")  # optional
    sql = SCHEMA_SQL
    if schema_path and os.path.exists(schema_path):
        with open(schema_path, "r", encoding="utf-8") as f:
            sql = f.read()

    with psycopg.connect(dsn, autocommit=False, row_factory=tuple_row) as conn:
        run_sql(conn, sql)
    print("✅ Schema (and seed) applied.")

if __name__ == "__main__":
    main()
