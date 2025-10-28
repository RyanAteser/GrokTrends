import os, psycopg2
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

# Raw tweets with engagement metrics
cur.execute('''
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
''')

# Topics extracted from tweets
cur.execute('''
    CREATE TABLE IF NOT EXISTS topics (
        id SERIAL PRIMARY KEY,
        topic_name VARCHAR(200),
        category VARCHAR(50),
        mentioned_at TIMESTAMP,
        tweet_id VARCHAR(50),
        confidence FLOAT DEFAULT 1.0,
        source VARCHAR(50) DEFAULT 'twitter'
    );
''')

# Daily trend aggregations
cur.execute('''
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
''')

# Hourly trend aggregations (for interest over time chart)
cur.execute('''
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
''')

# API usage tracking
cur.execute('''
    CREATE TABLE IF NOT EXISTS api_usage (
        id SERIAL PRIMARY KEY,
        query_date DATE DEFAULT CURRENT_DATE,
        posts_pulled INT,
        query_used VARCHAR(200),
        UNIQUE(query_date)
    );
''')

# Create indexes for performance
cur.execute('CREATE INDEX IF NOT EXISTS idx_topics_mentioned ON topics(mentioned_at);')
cur.execute('CREATE INDEX IF NOT EXISTS idx_topics_name ON topics(topic_name);')
cur.execute('CREATE INDEX IF NOT EXISTS idx_hourly_ts ON trend_agg_hourly(bucket_ts);')
cur.execute('CREATE INDEX IF NOT EXISTS idx_hourly_topic ON trend_agg_hourly(topic_name);')

conn.commit()
cur.close()
conn.close()
print('✅ Database initialized with all tables and indexes')