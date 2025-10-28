import os
import psycopg2
from datetime import datetime, timedelta
import random
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

print("🎨 Creating mock data for Grok Trends demo...\n")

# Realistic trending topics by category
topics_data = {
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

# Generate mock tweets and topics over last 7 days
now = datetime.now()
tweet_id_counter = 1000000

print("📝 Generating tweets and topics...")

for days_ago in range(7):
    tweet_date = now - timedelta(days=days_ago)
    
    # Generate 20-40 tweets per day
    num_tweets = random.randint(20, 40)
    
    for _ in range(num_tweets):
        # Random time within that day
        random_hour = random.randint(0, 23)
        random_minute = random.randint(0, 59)
        created_at = tweet_date.replace(hour=random_hour, minute=random_minute, second=0)
        
        # Pick random category and topic
        category = random.choice(list(topics_data.keys()))
        topic_name, base_mentions, base_growth = random.choice(topics_data[category])
        
        # Create tweet text
        templates = [
            f"Just asked Grok about {topic_name} and got some great insights!",
            f"Grok explained {topic_name} really well",
            f"Used Grok for help with {topic_name}",
            f"Anyone else using Grok for {topic_name}? Game changer!",
            f"Grok's take on {topic_name} is surprisingly good",
        ]
        text = random.choice(templates)
        
        # Insert tweet
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
            created_at,
            now,
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
        
        # Insert topic
        cur.execute("""
            INSERT INTO topics (topic_name, category, mentioned_at, tweet_id, confidence, source)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (
            topic_name,
            category,
            created_at,
            str(tweet_id_counter),
            0.8,
            'twitter'
        ))
        
        tweet_id_counter += 1

conn.commit()
print(f"✅ Created {tweet_id_counter - 1000000} tweets\n")

print("📊 Computing daily trends...")

# Compute daily aggregations
for category in topics_data.keys():
    for topic_name, mentions, growth in topics_data[category]:
        for days_ago in range(7):
            date = (now - timedelta(days=days_ago)).date()
            
            # Vary mentions per day
            daily_mentions = int(mentions / 7 * random.uniform(0.7, 1.3))
            daily_growth = growth + random.uniform(-20, 20)
            
            cur.execute("""
                INSERT INTO trend_aggregations (topic_name, category, date, mention_count, growth_rate)
                VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT (topic_name, category, date)
                DO UPDATE SET mention_count = EXCLUDED.mention_count, growth_rate = EXCLUDED.growth_rate
            """, (topic_name, category, date, daily_mentions, daily_growth))

conn.commit()
print("✅ Daily trends computed\n")

print("⏰ Computing hourly trends...")

# Compute hourly aggregations
for category in topics_data.keys():
    for topic_name, mentions, growth in topics_data[category]:
        # Last 72 hours
        for hours_ago in range(72):
            bucket_ts = now - timedelta(hours=hours_ago)
            bucket_ts = bucket_ts.replace(minute=0, second=0, microsecond=0)
            
            # Vary by hour (more activity during daytime)
            hour_of_day = bucket_ts.hour
            time_multiplier = 1.5 if 9 <= hour_of_day <= 17 else 0.7
            
            hourly_mentions = int(mentions / 168 * random.uniform(0.5, 1.5) * time_multiplier)
            hourly_weighted = int(hourly_mentions * random.uniform(1.0, 2.0))
            
            if hourly_mentions > 0:
                cur.execute("""
                    INSERT INTO trend_agg_hourly (bucket_ts, topic_name, category, mentions, weighted)
                    VALUES (%s, %s, %s, %s, %s)
                    ON CONFLICT (bucket_ts, topic_name, category)
                    DO UPDATE SET mentions = EXCLUDED.mentions, weighted = EXCLUDED.weighted
                """, (bucket_ts, topic_name, category, hourly_mentions, hourly_weighted))

conn.commit()
print("✅ Hourly trends computed\n")

# Log usage
cur.execute("""
    INSERT INTO api_usage (query_date, posts_pulled, query_used)
    VALUES (CURRENT_DATE, %s, %s)
    ON CONFLICT (query_date)
    DO UPDATE SET posts_pulled = api_usage.posts_pulled + EXCLUDED.posts_pulled
""", (tweet_id_counter - 1000000, "@Grok -is:retweet"))

conn.commit()

# Show summary
cur.execute("SELECT COUNT(*) FROM raw_tweets")
tweet_count = cur.fetchone()[0]

cur.execute("SELECT COUNT(*) FROM topics")
topic_count = cur.fetchone()[0]

cur.execute("SELECT COUNT(DISTINCT topic_name) FROM topics")
unique_topics = cur.fetchone()[0]

print("=" * 60)
print("📊 MOCK DATA SUMMARY")
print("=" * 60)
print(f"✅ Total tweets: {tweet_count}")
print(f"✅ Total topic mentions: {topic_count}")
print(f"✅ Unique topics: {unique_topics}")
print(f"✅ Date range: Last 7 days")
print(f"✅ Hourly data: Last 72 hours")
print("=" * 60)
print("\n🎉 Demo data ready! Start your API and frontend:\n")
print("   Terminal 1: python api.py")
print("   Terminal 2: cd web && npm run dev")
print("\n💡 Don't forget to add the 'Beta/Demo' banner to your frontend!")

cur.close()
conn.close()