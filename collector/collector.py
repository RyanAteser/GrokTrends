import os, re, time, psycopg2, tweepy
from datetime import datetime, timedelta
from psycopg2.extras import execute_values
from dotenv import load_dotenv

# =========================
# ASCII progress bar helpers
# =========================
import os, re, time, psycopg2, tweepy
from datetime import datetime, timedelta
from psycopg2.extras import execute_values
from dotenv import load_dotenv

# =========================
# ASCII progress bar helpers
# =========================
def _bar(percent: float, width: int = 30) -> str:
    percent = max(0.0, min(1.0, percent))
    filled = int(round(width * percent))
    return f"[{'#' * filled}{'-' * (width - filled)}] {int(percent * 100):3d}%"

def _countdown_bar(total_seconds: float, label: str = "Waiting", width: int = 30):
    total = max(0, int(round(total_seconds)))
    if total <= 0:
        return
    start = time.monotonic()
    deadline = start + total
    mins0, secs0 = divmod(total, 60)
    print(f"{label} {_bar(0.0, width)} {mins0:02d}:{secs0:02d}", end="\r", flush=True)
    while True:
        now = time.monotonic()
        remaining = deadline - now
        if remaining <= 0:
            print(" " * 100, end="\r")
            break
        elapsed = now - start
        percent = min(1.0, elapsed / total)
        rem = int(remaining + 0.5)
        mins, secs = divmod(rem, 60)
        print(f"{label} {_bar(percent, width)} {mins:02d}:{secs:02d}  ", end="\r", flush=True)
        time.sleep(min(1.0, max(0.05, remaining)))
    print()

class GrokTrendsCollector:
    def __init__(self):
        load_dotenv()
        self.conn = psycopg2.connect(
            host=os.getenv('PGHOST'),
            database=os.getenv('PGDATABASE'),
            user=os.getenv('PGUSER'),
            password=os.getenv('PGPASSWORD'),
            port=os.getenv('PGPORT', '5432'),
        )
        bearer = os.getenv('X_BEARER_TOKEN')
        if not bearer:
            raise RuntimeError('Set X_BEARER_TOKEN')
        self.twitter = tweepy.Client(bearer_token=bearer, wait_on_rate_limit=False)  # Changed to False

        self.queries = [
            '@Grok -is:retweet',
            '(to:@Grok OR from:@Grok OR mentions:@Grok) -is:retweet',
        ]

        self.categories = {
            'tech': ['code','programming','debug','software','algorithm','api','github','developer','bug','python','javascript','react'],
            'crypto': ['bitcoin','crypto','ethereum','blockchain','nft','defi','token','btc','eth','solana','web3'],
            'finance': ['stock','market','invest','trading','finance','portfolio','earnings','sp500','nasdaq','dow'],
            'news': ['news','breaking','update','headline','report','announcement','happening'],
            'culture': ['meme','trend','viral','tiktok','instagram','culture','pop','celebrity','movie','music'],
            'politics': ['politics','election','government','policy','congress','senate','president','vote','law'],
            'business': ['startup','business','entrepreneur','company','revenue','growth','venture','funding','ipo'],
            'science': ['research','study','science','biology','physics','climate','space','nasa','health'],
        }

    # ---------- DB / rate helpers ----------
    def monthly(self):
        cur = self.conn.cursor()
        cur.execute("""
            SELECT COALESCE(SUM(posts_pulled),0)
            FROM api_usage
            WHERE query_date >= DATE_TRUNC('month', CURRENT_DATE)
        """)
        v = cur.fetchone()[0]
        cur.close()
        return v

    def last_request_time(self):
        cur = self.conn.cursor()
        cur.execute('SELECT MAX(collected_at) FROM raw_tweets')
        result = cur.fetchone()[0]
        cur.close()
        return result if result else datetime.min

    def next_allowed_time(self):
        last = self.last_request_time()
        return datetime.now() if last == datetime.min else last + timedelta(minutes=15)

    def can_collect_now(self):
        return datetime.now() >= self.next_allowed_time()

    # ---------- Collection ----------
    def collect(self, max_results=100, block_on_rate_limit=False):
        allow_at = self.next_allowed_time()
        wait_seconds = (allow_at - datetime.now()).total_seconds()
        if wait_seconds > 0:
            if not block_on_rate_limit:
                mins, secs = divmod(int(wait_seconds + 0.5), 60)
                print(f'⏳ Rate limited. Wait {mins}:{secs:02d} more minutes')
                return []
            print("⏳ Rate limited. Waiting until the next allowed window…")
            _countdown_bar(wait_seconds, label="⏲ Time until next call")  # ← This line

        monthly = self.monthly()
        query_idx = (monthly // 100) % len(self.queries)
        q = self.queries[query_idx]
        print(f'🔍 Query: "{q}" (max {max_results} tweets)')
        print(f'📊 Month: ~{monthly} tweets collected')

        try:
            res = self.twitter.search_recent_tweets(
                query=q,
                max_results=max_results,
                tweet_fields=[
                    'created_at','author_id','lang','public_metrics',
                    'conversation_id','referenced_tweets'
                ],
                user_fields=['public_metrics','username','verified'],
                expansions=['author_id','referenced_tweets.id.author_id']
            )
        except Exception as e:
            print(f'❌ Twitter error: {e}')
            return []

        if not res.data:
            print('No tweets found')
            return []

        author_followers = {}
        try:
            if res.includes and 'users' in res.includes:
                for u in res.includes['users']:
                    uid = str(u.id)
                    followers = 0
                    if hasattr(u, 'public_metrics') and u.public_metrics:
                        followers = int(u.public_metrics.get('followers_count', 0))
                    author_followers[uid] = followers
        except Exception:
            pass

        cur = self.conn.cursor()
        added = 0
        for t in res.data:
            pm = getattr(t, 'public_metrics', {}) or {}
            like_count    = int(pm.get('like_count', 0))
            retweet_count = int(pm.get('retweet_count', 0))
            reply_count   = int(pm.get('reply_count', 0))
            quote_count   = int(pm.get('quote_count', 0))

            lang = getattr(t, 'lang', None)
            convo_id = getattr(t, 'conversation_id', None)
            author_id = str(getattr(t, 'author_id', '')) if getattr(t, 'author_id', None) else None
            followers = author_followers.get(author_id, 0)

            is_reply = False
            is_quote = False
            if getattr(t, 'referenced_tweets', None):
                for ref in t.referenced_tweets:
                    if ref.type == 'replied_to':
                        is_reply = True
                    elif ref.type == 'quoted':
                        is_quote = True

            try:
                cur.execute("""
                    INSERT INTO raw_tweets (
                        tweet_id, text, author_id, created_at, collected_at, search_query,
                        lang, conversation_id,
                        like_count, retweet_count, reply_count, quote_count,
                        author_followers, is_quote, is_reply
                    )
                    VALUES (%s,%s,%s,%s, NOW(), %s,
                            %s,%s,
                            %s,%s,%s,%s,
                            %s,%s,%s)
                    ON CONFLICT (tweet_id) DO NOTHING
                """, (
                    str(t.id), t.text, author_id, t.created_at, q,
                    lang, convo_id,
                    like_count, retweet_count, reply_count, quote_count,
                    followers, is_quote, is_reply
                ))
                if cur.rowcount > 0:
                    added += 1
            except Exception as e:
                print(f'Insert error: {e}')

        cur.execute("""
            INSERT INTO api_usage (query_date, posts_pulled, query_used)
            VALUES (CURRENT_DATE, %s, %s)
            ON CONFLICT (query_date)
            DO UPDATE SET posts_pulled = api_usage.posts_pulled + EXCLUDED.posts_pulled
        """, (added, q))

        self.conn.commit()
        cur.close()
        print(f'✅ Collected {added} new tweets')
        print(f'⏰ Next request available at {(datetime.now() + timedelta(minutes=15)).strftime("%H:%M:%S")}')
        return res.data

    # ---------- Topic extraction ----------
    def extract_topics(self, text):
        text_lower = text.lower()
        found = []
        patterns = [
            r'about ([^.!?\n]{3,50})',
            r'for ([^.!?\n]{3,50})',
            r'explained ([^.!?\n]{3,50})',
            r'help with ([^.!?\n]{3,50})'
        ]
        for pattern in patterns:
            for match in re.findall(pattern, text_lower):
                topic = match.strip()
                if len(topic) > 3 and not topic.startswith(('http','@','#')):
                    category = self.categorize(topic)
                    found.append((topic, category, 0.8))
        for category, keywords in self.categories.items():
            for keyword in keywords:
                if keyword in text_lower:
                    found.append((keyword, category, 0.6))
        return found

    def categorize(self, topic):
        tl = topic.lower()
        for category, keywords in self.categories.items():
            if any(kw in tl for kw in keywords):
                return category
        return 'general'

    # ---------- Processing / trends ----------
    def process_topics(self):
        cur = self.conn.cursor()
        cur.execute("""
            SELECT t.tweet_id, t.text, t.created_at
            FROM raw_tweets t
            LEFT JOIN topics top ON t.tweet_id = top.tweet_id
            WHERE top.id IS NULL
        """)
        rows = cur.fetchall()
        if not rows:
            print('No unprocessed tweets')
            cur.close()
            return
        print(f'📊 Processing {len(rows)} tweets...')

        batch = []
        for tweet_id, text, created_at in rows:
            for topic_name, category, confidence in self.extract_topics(text):
                batch.append((topic_name, category, created_at, tweet_id, confidence, 'twitter'))
        if batch:
            execute_values(cur, """
                INSERT INTO topics (topic_name, category, mentioned_at, tweet_id, confidence, source)
                VALUES %s
            """, batch)
            print(f'✅ Extracted {len(batch)} topics')

        self.conn.commit()
        cur.close()

    def compute_trends(self):
        cur = self.conn.cursor()
        cur.execute("""
            INSERT INTO trend_aggregations (topic_name, category, date, mention_count, growth_rate)
            SELECT topic_name, category, DATE(mentioned_at), COUNT(*), 0.0
            FROM topics
            WHERE DATE(mentioned_at) >= CURRENT_DATE - INTERVAL '7 days'
            GROUP BY topic_name, category, DATE(mentioned_at)
            ON CONFLICT (topic_name, category, date)
            DO UPDATE SET mention_count = EXCLUDED.mention_count, computed_at = NOW()
        """)
        cur.execute("""
            WITH today AS (
                SELECT topic_name, category, mention_count AS today_count
                FROM trend_aggregations WHERE date = CURRENT_DATE
            ),
            yesterday AS (
                SELECT topic_name, category, mention_count AS yesterday_count
                FROM trend_aggregations WHERE date = CURRENT_DATE - INTERVAL '1 day'
            )
            UPDATE trend_aggregations ta
            SET growth_rate = CASE
                WHEN y.yesterday_count > 0
                THEN ((t.today_count - y.yesterday_count) * 100.0 / y.yesterday_count)
                ELSE 100.0
            END
            FROM today t
            LEFT JOIN yesterday y ON t.topic_name = y.topic_name AND t.category = y.category
            WHERE ta.topic_name = t.topic_name AND ta.category = t.category AND ta.date = CURRENT_DATE
        """)
        self.conn.commit()
        cur.close()
        print('✅ Trends computed')
    def compute_hourly_trends(self):
        """Aggregate topics into hourly buckets for interest-over-time chart"""
        cur = self.conn.cursor()

        # First check what columns exist
        cur.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'raw_tweets' AND column_name LIKE '%like%'
        """)
        print(f"Available columns: {cur.fetchall()}")

        # Aggregate topics by hour with weighted scoring
        cur.execute("""
            WITH hourly_raw AS (
                SELECT 
                    date_trunc('hour', t.mentioned_at) AS bucket_ts,
                    t.topic_name,
                    t.category,
                    COUNT(*) AS mentions,
                    -- Weighted score based on engagement (using correct column names)
                    SUM(
                        CASE 
                            WHEN rt.like_count IS NOT NULL 
                            THEN 1 + (rt.like_count * 0.1) + (rt.retweet_count * 0.5)
                            ELSE 1 
                        END
                    ) AS weighted
                FROM topics t
                LEFT JOIN raw_tweets rt ON t.tweet_id = rt.tweet_id
                WHERE t.mentioned_at >= NOW() - INTERVAL '30 days'
                GROUP BY bucket_ts, t.topic_name, t.category
            )
            INSERT INTO trend_agg_hourly (bucket_ts, topic_name, category, mentions, weighted)
            SELECT bucket_ts, topic_name, category, mentions::INT, weighted::INT
            FROM hourly_raw
            ON CONFLICT (bucket_ts, topic_name, category)
            DO UPDATE SET
                mentions = EXCLUDED.mentions,
                weighted = EXCLUDED.weighted,
                computed_at = NOW()
        """)

        self.conn.commit()
        cur.close()
        print('✅ Hourly trends computed')
    def show_top_trends(self, limit=5):
        cur = self.conn.cursor()
        cur.execute("""
            SELECT topic_name, category, SUM(mention_count) AS total, AVG(growth_rate) AS avg_growth
            FROM trend_aggregations
            WHERE date >= CURRENT_DATE - INTERVAL '7 days'
            GROUP BY topic_name, category
            ORDER BY total DESC, avg_growth DESC
            LIMIT %s
        """, (limit,))
        trends = cur.fetchall()
        cur.close()

        if trends:
            print('\n🔥 Top Trends (Last 7 Days):')
            for i, (topic, cat, mentions, growth) in enumerate(trends, 1):
                print(f'{i}. {topic} ({cat}) - {mentions} mentions, {growth:+.1f}% growth')
        else:
            print('No trends yet - need more data!')

    # ---------- Orchestration ----------
    def run(self, block_on_rate_limit: bool = False):
        print(f'\n{"=" * 60}')
        print(f'🚀 Grok Trends Collection - {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}')
        print(f'{"=" * 60}\n')

        tweets = self.collect(block_on_rate_limit=block_on_rate_limit)
        if tweets:
            self.process_topics()
            self.compute_trends()
            self.compute_hourly_trends()  # ← Add this line
            self.show_top_trends()
        print(f'\n{"=" * 60}\n')

    def close(self):
        try:
            self.conn.close()
        except:
            pass

if __name__ == "__main__":
    c = GrokTrendsCollector()
    try:
        c.run(block_on_rate_limit=True)
    finally:
        c.close()
