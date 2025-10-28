# seed_all.py
# One-shot seeder for Grok Trends (schema + mock data)
# Works on Render/Supabase/Neon/etc using DATABASE_URL (psycopg v3)

import os
import random
import argparse
from datetime import datetime, timedelta, timezone
from urllib.parse import urlparse, parse_qsl, urlencode, urlunparse

import psycopg

# ---------- Connection helpers (psycopg v3) ----------

def _ensure_ssl_in_dsn(dsn: str) -> str:
    """Append sslmode=require to a DATABASE_URL if not present."""
    p = urlparse(dsn)
    q = dict(parse_qsl(p.query, keep_blank_values=True))
    q.setdefault("sslmode", os.getenv("PGSSLMODE", "require"))
    return urlunparse(p._replace(query=urlencode(q)))

def get_conn():
    dsn = os.getenv("DATABASE_URL")
    if not dsn:
        raise RuntimeError("DATABASE_URL is not set. Add it in Render → Environment.")
    dsn = _ensure_ssl_in_dsn(dsn)
    return psycopg.connect(dsn, autocommit=False)

# ---------- Schema (tables + indexes) ----------

DDL = """
-- Raw tweets with engagement metrics
CREATE TABLE IF NOT EXISTS raw_tweets (
    id SERIAL PRIMARY KEY,
    tweet_id VARCHAR(50) UNIQUE,
    text TEXT,
    author_id VARCHAR(50),
    created_at TIMESTAMP,
    collected_at TIMESTAMP DEFAULT NOW(),
    search_query VARCHAR(200),
    lang VARCHAR(10),
    conversation_id VARCHAR(50),
    like_count INT DEFAULT 0,
    retweet_count INT DEFAULT 0,
    reply_count INT DEFAULT 0,
    quote_count INT DEFAULT 0,
    author_followers INT DEFAULT 0,
    is_quote BOOLEAN DEFAULT FALSE,
    is_reply BOOLEAN DEFAULT FALSE
);

-- Topics extracted from tweets
CREATE TABLE IF NOT EXISTS topics (
    id SERIAL PRIMARY KEY,
    topic_name VARCHAR(200),
    category VARCHAR(50),
    mentioned_at TIMESTAMP,
    tweet_id VARCHAR(50),
    confidence FLOAT DEFAULT 1.0,
    source VARCHAR(50) DEFAULT 'twitter'
);

-- Daily trend aggregations
CREATE TABLE IF NOT EXISTS trend_aggregations (
    id SERIAL PRIMARY KEY,
    topic_name VARCHAR(200),
    category VARCHAR(50),
    date DATE,
    mention_count INT,
    growth_rate FLOAT,
    computed_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(topic_name, category, date)
);

-- Hourly trend aggregations (for interest over time chart)
CREATE TABLE IF NOT EXISTS trend_agg_hourly (
    id SERIAL PRIMARY KEY,
    bucket_ts TIMESTAMP,
    topic_name VARCHAR(200),
    category VARCHAR(50),
    mentions INT DEFAULT 0,
    weighted INT DEFAULT 0,
    computed_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(bucket_ts, topic_name, category)
);

-- API usage tracking
CREATE TABLE IF NOT EXISTS api_usage (
    id SERIAL PRIMARY KEY,
    query_date DATE DEFAULT CURRENT_DATE,
    posts_pulled INT,
    query_used VARCHAR(200),
    UNIQUE(query_date)
);

-- Interest signups
CREATE TABLE IF NOT EXISTS interest_signups (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    referrer VARCHAR(100),
    user_agent TEXT
);

-- Indexes for perf
CREATE INDEX IF NOT EXISTS idx_topics_mentioned ON topics(mentioned_at);
CREATE INDEX IF NOT EXISTS idx_topics_name ON topics(topic_name);
CREATE INDEX IF NOT EXISTS idx_hourly_ts ON trend_agg_hourly(bucket_ts);
CREATE INDEX IF NOT EXISTS idx_hourly_topic ON trend_agg_hourly(topic_name);
"""

def create_schema(conn):
    with conn.cursor() as cur:
        cur.execute(DDL)
    conn.commit()
    print("✅ Schema created / verified")

# ---------- Mock data ----------

TOPICS_DATA = {
    'tech': [
        ('python debugging', 45, 156),
        ('react hooks', 38, 89),
        ('api integration', 34, 112),
        ('code review', 28, 78),
        ('git merge conflict', 25, 145),
        ('typescript types', 22, 67),
        ('docker containers', 19, 94),
        ('unit testing', 17, 56),
        ('microservices', 15, 123),
        ('GraphQL queries', 12, 88),
    ],
    'crypto': [
        ('bitcoin price', 52, 234),
        ('ethereum gas fees', 41, 178),
        ('defi yield farming', 35, 156),
        ('NFT marketplace', 29, 134),
        ('solana transactions', 24, 98),
        ('crypto wallet security', 21, 167),
        ('blockchain technology', 18, 112),
        ('web3 development', 16, 89),
        ('token economics', 13, 76),
        ('crypto regulations', 11, 145),
    ],
    'finance': [
        ('stock market analysis', 48, 189),
        ('investment strategy', 36, 145),
        ('portfolio diversification', 31, 123),
        ('trading indicators', 27, 167),
        ('retirement planning', 23, 98),
        ('real estate investment', 19, 134),
        ('crypto vs stocks', 16, 156),
        ('tax optimization', 14, 112),
        ('dividend stocks', 12, 89),
        ('options trading', 10, 178),
    ],
    'news': [
        ('AI regulation news', 58, 267),
        ('tech layoffs', 44, 198),
        ('climate change updates', 37, 176),
        ('election coverage', 32, 234),
        ('space exploration', 26, 145),
        ('breaking tech news', 21, 189),
        ('economic indicators', 18, 156),
        ('healthcare policy', 15, 123),
        ('cybersecurity threats', 13, 198),
        ('social media trends', 11, 134),
    ],
    'culture': [
        ('viral memes', 61, 312),
        ('celebrity gossip', 47, 245),
        ('movie reviews', 39, 189),
        ('music recommendations', 33, 167),
        ('trending TikTok', 28, 234),
        ('gaming news', 24, 198),
        ('fashion trends', 20, 145),
        ('food recipes', 17, 156),
        ('travel destinations', 14, 123),
        ('pop culture debates', 12, 178),
    ],
    'politics': [
        ('election polls', 55, 278),
        ('policy analysis', 42, 212),
        ('political debates', 36, 189),
        ('government spending', 30, 167),
        ('voting rights', 25, 145),
        ('international relations', 21, 198),
        ('supreme court', 18, 156),
        ('congressional bills', 15, 134),
        ('campaign finance', 12, 123),
        ('political scandals', 10, 212),
    ],
    'business': [
        ('startup funding', 49, 223),
        ('entrepreneurship tips', 40, 189),
        ('business strategy', 34, 167),
        ('venture capital', 29, 145),
        ('company valuations', 24, 198),
        ('market trends', 20, 156),
        ('remote work', 17, 134),
        ('productivity hacks', 14, 178),
        ('leadership skills', 12, 123),
        ('growth hacking', 10, 212),
    ],
    'science': [
        ('AI research', 53, 245),
        ('climate science', 43, 198),
        ('space discoveries', 37, 178),
        ('medical breakthroughs', 31, 156),
        ('quantum computing', 26, 189),
        ('genetic engineering', 22, 145),
        ('renewable energy', 19, 167),
        ('neuroscience', 16, 134),
        ('physics discoveries', 13, 123),
        ('ocean exploration', 11, 198),
    ],
}

def seed_data(conn, days: int, hours: int, min_tweets: int, max_tweets: int):
    tz_now = datetime.now(timezone.utc)
    tweet_id_counter = 1_000_000
    total_tweets_inserted = 0

    print("📝 Generating tweets and topics...")
    with conn.cursor() as cur:
        for days_ago in range(days):
            base_day = tz_now - timedelta(days=days_ago)

            num_tweets = random.randint(min_tweets, max_tweets)
            for _ in range(num_tweets):
                # Spread in 24h of that day (UTC)
                created_at = (base_day.replace(hour=0, minute=0, second=0, microsecond=0)
                              + timedelta(minutes=random.randint(0, 24*60 - 1)))
                category = random.choice(list(TOPICS_DATA.keys()))
                topic_name, base_mentions, base_growth = random.choice(TOPICS_DATA[category])
                templates = [
                    f"Just asked Grok about {topic_name} and got some great insights!",
                    f"Grok explained {topic_name} really well",
                    f"Used Grok for help with {topic_name}",
                    f"Anyone else using Grok for {topic_name}? Game changer!",
                    f"Grok's take on {topic_name} is surprisingly good",
                ]
                text = random.choice(templates)

                cur.execute("""
                    INSERT INTO raw_tweets (
                        tweet_id, text, author_id, created_at, collected_at, search_query,
                        lang, like_count, retweet_count, reply_count, quote_count,
                        author_followers, is_quote, is_reply
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (tweet_id) DO NOTHING
                """, (
                    str(tweet_id_counter),
                    text,
                    f"user_{random.randint(1000, 9999)}",
                    created_at.replace(tzinfo=None),  # store naive UTC
                    tz_now.replace(tzinfo=None),
                    "@Grok -is:retweet",
                    "en",
                    random.randint(0, 50),
                    random.randint(0, 20),
                    random.randint(0, 10),
                    random.randint(0, 5),
                    random.randint(100, 10000),
                    False,
                    False
                ))

                cur.execute("""
                    INSERT INTO topics (topic_name, category, mentioned_at, tweet_id, confidence, source)
                    VALUES (%s, %s, %s, %s, %s, %s)
                """, (
                    topic_name,
                    category,
                    created_at.replace(tzinfo=None),
                    str(tweet_id_counter),
                    0.8,
                    'twitter'
                ))

                tweet_id_counter += 1
                total_tweets_inserted += 1

        conn.commit()
    print(f"✅ Created {total_tweets_inserted} tweets/topics\n")

    print("📊 Computing daily trends...")
    with conn.cursor() as cur:
        for category, topics in TOPICS_DATA.items():
            for topic_name, mentions, growth in topics:
                for days_ago in range(days):
                    date = (tz_now - timedelta(days=days_ago)).date()
                    # Some variation per day
                    daily_mentions = max(1, int(mentions / max(days,1) * random.uniform(0.7, 1.3)))
                    daily_growth = growth + random.uniform(-20, 20)

                    cur.execute("""
                        INSERT INTO trend_aggregations (topic_name, category, date, mention_count, growth_rate)
                        VALUES (%s, %s, %s, %s, %s)
                        ON CONFLICT (topic_name, category, date)
                        DO UPDATE SET
                            mention_count = EXCLUDED.mention_count,
                            growth_rate   = EXCLUDED.growth_rate,
                            computed_at   = NOW()
                    """, (topic_name, category, date, daily_mentions, daily_growth))
        conn.commit()
    print("✅ Daily trends computed\n")

    print("⏰ Computing hourly trends...")
    with conn.cursor() as cur:
        for category, topics in TOPICS_DATA.items():
            for topic_name, mentions, growth in topics:
                for h in range(hours):
                    bucket_ts = (tz_now - timedelta(hours=h)).replace(minute=0, second=0, microsecond=0)
                    hour_of_day = bucket_ts.hour
                    time_multiplier = 1.5 if 9 <= hour_of_day <= 17 else 0.7
                    # Roughly scale mentions across hours
                    hourly_mentions = int(max(1, (mentions / max(7*24,1)) * random.uniform(0.5, 1.5) * time_multiplier))
                    hourly_weighted = int(max(1, hourly_mentions * random.uniform(1.0, 2.0)))

                    cur.execute("""
                        INSERT INTO trend_agg_hourly (bucket_ts, topic_name, category, mentions, weighted)
                        VALUES (%s, %s, %s, %s, %s)
                        ON CONFLICT (bucket_ts, topic_name, category)
                        DO UPDATE SET
                            mentions = EXCLUDED.mentions,
                            weighted = EXCLUDED.weighted,
                            computed_at = NOW()
                    """, (bucket_ts.replace(tzinfo=None), topic_name, category, hourly_mentions, hourly_weighted))
        conn.commit()
    print("✅ Hourly trends computed\n")

    # Log usage
    with conn.cursor() as cur:
        cur.execute("""
            INSERT INTO api_usage (query_date, posts_pulled, query_used)
            VALUES (CURRENT_DATE, %s, %s)
            ON CONFLICT (query_date)
            DO UPDATE SET posts_pulled = api_usage.posts_pulled + EXCLUDED.posts_pulled
        """, (total_tweets_inserted, "@Grok -is:retweet"))
    conn.commit()

    # Summary
    with conn.cursor() as cur:
        cur.execute("SELECT COUNT(*) FROM raw_tweets")
        tweet_count = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM topics")
        topic_count = cur.fetchone()[0]
        cur.execute("SELECT COUNT(DISTINCT topic_name) FROM topics")
        unique_topics = cur.fetchone()[0]

    print("=" * 60)
    print("📊 MOCK DATA SUMMARY")
    print("=" * 60)
    print(f"✅ Total tweets:       {tweet_count}")
    print(f"✅ Total topic rows:   {topic_count}")
    print(f"✅ Unique topics:      {unique_topics}")
    print(f"✅ Days seeded:        {days}")
    print(f"✅ Hours seeded:       {hours}")
    print("=" * 60)
    print("\n🎉 Demo data ready! Endpoints to try:")
    print("   • /health")
    print("   • /api/trends?days=7&limit=10")
    print("   • /api/categories")
    print("   • /api/interest?topics=python%20debugging&topics=react%20hooks&hours=48\n")

# ---------- CLI ----------

def parse_args():
    ap = argparse.ArgumentParser(description="Seed Grok Trends schema and mock data.")
    ap.add_argument("--days", type=int, default=7, help="How many past days to seed (default: 7)")
    ap.add_argument("--hours", type=int, default=72, help="How many past hours to seed (default: 72)")
    ap.add_argument("--min-tweets", type=int, default=20, help="Min tweets per day (default: 20)")
    ap.add_argument("--max-tweets", type=int, default=40, help="Max tweets per day (default: 40)")
    return ap.parse_args()

def main():
    args = parse_args()
    if args.min_tweets > args.max_tweets:
        raise SystemExit("--min-tweets cannot be greater than --max-tweets")

    with get_conn() as conn:
        create_schema(conn)
        seed_data(conn, days=args.days, hours=args.hours,
                  min_tweets=args.min_tweets, max_tweets=args.max_tweets)

if __name__ == "__main__":
    main()
