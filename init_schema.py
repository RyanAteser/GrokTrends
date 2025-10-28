# 1) init_schema.py  (creates tables & indexes)
import psycopg
from connector import get_conn

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

-- Hourly trend aggregations
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

-- Indexes
CREATE INDEX IF NOT EXISTS idx_topics_mentioned ON topics(mentioned_at);
CREATE INDEX IF NOT EXISTS idx_topics_name ON topics(topic_name);
CREATE INDEX IF NOT EXISTS idx_hourly_ts ON trend_agg_hourly(bucket_ts);
CREATE INDEX IF NOT EXISTS idx_hourly_topic ON trend_agg_hourly(topic_name);
"""

def main():
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute(DDL)
    print("✅ Schema created.")

if __name__ == "__main__":
    main()
