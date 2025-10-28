# db.py
import os
from urllib.parse import urlparse, parse_qsl, urlencode, urlunparse
import psycopg2
import psycopg2.pool

_POOL = None

def _ensure_ssl_in_dsn(dsn: str) -> str:
    # Append sslmode=require if no sslmode present
    parsed = urlparse(dsn)
    q = dict(parse_qsl(parsed.query, keep_blank_values=True))
    if "sslmode" not in q:
        q["sslmode"] = os.getenv("PGSSLMODE", "require")
    new_q = urlencode(q)
    return urlunparse(parsed._replace(query=new_q))

def make_pool():
    global _POOL
    if _POOL is not None:
        return _POOL

    maxconn = int(os.getenv("PGPOOL_MAX", "5"))

    dsn = os.getenv("DATABASE_URL")
    if dsn:
        dsn = _ensure_ssl_in_dsn(dsn)
        _POOL = psycopg2.pool.SimpleConnectionPool(
            minconn=1,
            maxconn=maxconn,
            dsn=dsn,
            # TCP keepalives (recommended for PaaS)
            keepalives=1,
            keepalives_idle=30,
            keepalives_interval=10,
            keepalives_count=5,
        )
        return _POOL

    # Discrete vars (local dev)
    _POOL = psycopg2.pool.SimpleConnectionPool(
        minconn=1,
        maxconn=maxconn,
        host=os.getenv("PGHOST", "localhost"),
        database=os.getenv("PGDATABASE", "postgres"),
        user=os.getenv("PGUSER", "postgres"),
        password=os.getenv("PGPASSWORD", ""),
        port=os.getenv("PGPORT", "5432"),
        sslmode=os.getenv("PGSSLMODE", "disable"),
        keepalives=1,
        keepalives_idle=30,
        keepalives_interval=10,
        keepalives_count=5,
    )
    return _POOL

def get_conn():
    pool = make_pool()
    try:
        conn = pool.getconn()
        # optional: ensure sane defaults each checkout
        with conn.cursor() as cur:
            cur.execute("SET TIME ZONE 'UTC'")
            cur.execute("SET statement_timeout = 60000")  # 60s
        return conn
    except Exception as e:
        raise RuntimeError(f"DB pool error: {e}")

def put_conn(conn):
    try:
        make_pool().putconn(conn)
    except Exception:
        try:
            conn.close()
        except Exception:
            pass

def close_pool():
    global _POOL
    if _POOL:
        try:
            _POOL.closeall()
        finally:
            _POOL = None

def ping():
    # simple healthcheck for /health
    conn = None
    try:
        conn = get_conn()
        with conn.cursor() as cur:
            cur.execute("SELECT 1")
            return True
    except Exception:
        return False
    finally:
        if conn:
            put_conn(conn)
