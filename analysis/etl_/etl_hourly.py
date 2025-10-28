import os, math, psycopg2
from datetime import datetime, timedelta, timezone
from psycopg2.extras import execute_values
from dotenv import load_dotenv

load_dotenv()

def get_db():
    return psycopg2.connect(
        host=os.getenv('PGHOST'),
        database=os.getenv('PGDATABASE'),
        user=os.getenv('PGUSER'),
        password=os.getenv('PGPASSWORD'),
        port=os.getenv('PGPORT', '5432')
    )

def clamp(v, lo, hi):
    return max(lo, min(hi, v))

def engagement_weight(like_count, retweet_count, reply_count, quote_count, author_followers):
    base = 1.0
    inter = like_count + (2 * retweet_count) + reply_count + quote_count
    part_inter = clamp(math.log2(1 + inter), 0.0, 3.0)
    part_follow = clamp(math.log10(1 + max(0, author_followers)), 0.0, 3.0)
    return base + part_inter + part_follow

def ensure_table(conn):
    cur = conn.cursor()
    cur.execute("""
    CREATE TABLE IF NOT EXISTS trend_agg_hourly (
      topic_name   TEXT NOT NULL,
      category     TEXT NOT NULL,
      bucket_ts    TIMESTAMPTZ NOT NULL,
      mentions     INT NOT NULL DEFAULT 0,
      weighted     DOUBLE PRECISION NOT NULL DEFAULT 0.0,
      PRIMARY KEY (topic_name, category, bucket_ts)
    );
    """)
    cur.execute("CREATE INDEX IF NOT EXISTS idx_trend_agg_hourly_ts ON trend_agg_hourly(bucket_ts);")
    conn.commit()
    cur.close()

def fetch_topic_events(conn, since_ts):
    cur = conn.cursor()
    cur.execute("""
        SELECT
          top.topic_name,
          top.category,
          date_trunc('hour', top.mentioned_at AT TIME ZONE 'UTC') AS bucket_ts,
          COALESCE(rt.like_count,0),
          COALESCE(rt.retweet_count,0),
          COALESCE(rt.reply_count,0),
          COALESCE(rt.quote_count,0),
          COALESCE(rt.author_followers,0)
        FROM topics top
        JOIN raw_tweets rt ON rt.tweet_id = top.tweet_id
        WHERE top.mentioned_at >= %s
    """, (since_ts,))
    rows = cur.fetchall()
    cur.close()
    return rows

def aggregate(rows):
    agg = {}
    for topic, cat, bucket_ts, likes, rts, replies, quotes, followers in rows:
        key = (topic, cat, bucket_ts)
        w = engagement_weight(likes, rts, replies, quotes, followers)
        if key not in agg:
            agg[key] = [0, 0.0]
        agg[key][0] += 1
        agg[key][1] += w
    return agg

def upsert_hourly(conn, agg):
    cur = conn.cursor()
    rows = [
        (topic, cat, bucket_ts, mentions, weighted)
        for (topic, cat, bucket_ts), (mentions, weighted) in agg.items()
    ]
    if rows:
        execute_values(cur, """
            INSERT INTO trend_agg_hourly (topic_name, category, bucket_ts, mentions, weighted)
            VALUES %s
            ON CONFLICT (topic_name, category, bucket_ts)
            DO UPDATE SET
              mentions = EXCLUDED.mentions,
              weighted = EXCLUDED.weighted
        """, rows, template="(%s,%s,%s,%s,%s)")
    conn.commit()
    cur.close()

def backfill_and_update(hours_back=48):
    conn = get_db()
    try:
        ensure_table(conn)
        now_utc = datetime.now(timezone.utc)
        since_ts = now_utc - timedelta(hours=hours_back)
        print(f"⏳ ETL: aggregating since {since_ts.isoformat()} (last {hours_back}h)")
        events = fetch_topic_events(conn, since_ts)
        if not events:
            print("… no topic events found in the window.")
            return
        agg = aggregate(events)
        upsert_hourly(conn, agg)
        print(f"✅ Upserted {len(agg)} hourly topic buckets.")
    finally:
        conn.close()

def compute_interest_index(conn, topics, hours_back=48, use_weighted=True):
    metric = "weighted" if use_weighted else "mentions"
    cur = conn.cursor()
    cur.execute(f"""
        WITH params AS (
            SELECT date_trunc('hour', NOW() AT TIME ZONE 'UTC') AS now_hr,
                   %s::INT AS hours_back
        ),
        series AS (
            SELECT generate_series(
                (SELECT now_hr - (hours_back || ' hours')::interval FROM params),
                (SELECT now_hr FROM params),
                '1 hour'::interval
            ) AS bucket_ts
        ),
        raw AS (
            SELECT ta.bucket_ts, ta.topic_name, ta.category, ta.{metric} AS v
            FROM trend_agg_hourly ta
            WHERE ta.bucket_ts >= (SELECT MIN(bucket_ts) FROM series)
              AND ta.topic_name = ANY(%s)
        ),
        joined AS (
            SELECT s.bucket_ts, r.topic_name, r.category, COALESCE(r.v, 0) AS v
            FROM series s
            LEFT JOIN raw r ON r.bucket_ts = s.bucket_ts
        ),
        maxes AS (
            SELECT topic_name, category, MAX(v) AS vmax
            FROM joined
            GROUP BY topic_name, category
        )
        SELECT j.bucket_ts, j.topic_name, j.category,
               CASE WHEN m.vmax > 0 THEN ROUND(100.0 * j.v / m.vmax)::INT ELSE 0 END AS index_0_100
        FROM joined j
        JOIN maxes m USING (topic_name, category)
        ORDER BY j.bucket_ts ASC, j.topic_name ASC;
    """, (hours_back, topics))
    data = cur.fetchall()
    cur.close()
    return data

if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser(description="Build hourly topic aggregates and Interest Over Time index.")
    ap.add_argument("--hours", type=int, default=48, help="Backfill window (hours)")
    ap.add_argument("--preview", nargs="*", help="Optional: preview 0-100 series for these topics")
    ap.add_argument("--mentions", action="store_true", help="Use raw mentions instead of weighted engagement")
    args = ap.parse_args()

    backfill_and_update(hours_back=args.hours)

    if args.preview:
        conn = get_db()
        try:
            rows = compute_interest_index(conn, topics=args.preview, hours_back=args.hours, use_weighted=not args.mentions)
            if not rows:
                print("No data for preview topics in the selected window.")
            else:
                print("\n📈 Interest Over Time (0–100):")
                last_ts, line = None, ""
                for ts, topic, cat, idx in rows:
                    if ts != last_ts:
                        if line:
                            print(line)
                        line = ts.strftime("%Y-%m-%d %H:%M") + "  "
                        last_ts = ts
                    line += f"{topic}={idx:3d}  "
                if line:
                    print(line)
        finally:
            conn.close()
