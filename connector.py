# connector.py (shared helper)
import os, psycopg
from urllib.parse import urlparse, parse_qsl, urlencode, urlunparse

def build_dsn():
    dsn = os.getenv("DATABASE_URL")
    if not dsn:
        raise RuntimeError("DATABASE_URL is not set")
    # Ensure SSL in cloud
    parsed = urlparse(dsn)
    q = dict(parse_qsl(parsed.query, keep_blank_values=True))
    q.setdefault("sslmode", "require")
    return urlunparse(parsed._replace(query=urlencode(q)))

def get_conn():
    return psycopg.connect(build_dsn(), autocommit=False)
