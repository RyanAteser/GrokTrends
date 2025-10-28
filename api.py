# app.py
import os
from datetime import datetime
from typing import List, Optional

import psycopg2
import psycopg2.pool
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr
from dotenv import load_dotenv

load_dotenv()

# ---------- DB POOL ----------
def make_pool():
    dsn = os.getenv("DATABASE_URL")
    if dsn:
        # Render/Neon/Heroku style, force SSL when hosted
        return psycopg2.pool.SimpleConnectionPool(
            minconn=1,
            maxconn=int(os.getenv("PGPOOL_MAX", "5")),
            dsn=dsn,
            sslmode=os.getenv("PGSSLMODE", "require"),
        )
    # Discrete vars fallback (local dev)
    host = os.getenv("PGHOST", "localhost")
    db = os.getenv("PGDATABASE", "postgres")
    user = os.getenv("PGUSER", "postgres")
    pwd = os.getenv("PGPASSWORD", "")
    port = os.getenv("PGPORT", "5432")
    return psycopg2.pool.SimpleConnectionPool(
        minconn=1,
        maxconn=int(os.getenv("PGPOOL_MAX", "5")),
        host=host,
        database=db,
        user=user,
        password=pwd,
        port=port,
        sslmode=os.getenv("PGSSLMODE", "disable"),
    )

POOL = make_pool()

def get_conn():
    try:
        return POOL.getconn()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"DB pool error: {e}")

def put_conn(conn):
    try:
        POOL.putconn(conn)
    except Exception:
        try:
            conn.close()
        except Exception:
            pass

# ---------- APP ----------
app = FastAPI(title="Grok Trends API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://localhost:3000",
        "https://grok-trends.vercel.app",
        "https://groktrends.com",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def root():
    return {
        "name": "Grok Trends API",
        "version": "1.0.0",
        "endpoints": {
            "/api/trends": "Get trending topics and chart data",
            "/api/topics/search": "Search topics",
            "/api/stats": "Get platform statistics",
            "/api/categories": "Category rollups",
            "/api/interest": "Hourly 0–100 index series",
            "/health": "Health check",
        },
    }

@app.get("/health")
def health_check():
    conn = None
    try:
        conn = get_conn()
        with conn.cursor() as cur:
            cur.execute("SELECT 1")
            ok = cur.fetchone()[0] == 1
        return {"status": "healthy" if ok else "degraded", "database": "connected"}
    except Exception as e:
        return {"status": "unhealthy", "error": str(e)}
    finally:
        if conn:
            put_conn(conn)

# ---------- QUERIES ----------
@app.get("/api/trends")
def get_trends(
        days: int = Query(7, ge=1, le=90),
        category: Optional[str] = Query(None),
        limit: int = Query(20, ge=1, le=100),
):
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            # Build filters
            params = [days]
            cat_sql = ""
            if category and category != "all":
                cat_sql = "AND category = %s"
                params.append(category)
            params.append(limit)

            # NOTE: use INTERVAL '1 day' * %s instead of "INTERVAL '%s days'"
            cur.execute(
                f"""
                SELECT topic_name, category,
                       SUM(mention_count) AS total_mentions,
                       AVG(growth_rate)   AS avg_growth
                FROM trend_aggregations
                WHERE date >= CURRENT_DATE - INTERVAL '1 day' * %s
                {cat_sql}
                GROUP BY topic_name, category
                ORDER BY total_mentions DESC, avg_growth DESC
                LIMIT %s
                """,
                params,
            )
            topics_raw = cur.fetchall()

            trending_topics = [
                {
                    "topic": t,
                    "category": c,
                    "mentions": int(m),
                    "growth": round(float(g or 0), 1),
                    "rank": i + 1,
                }
                for i, (t, c, m, g) in enumerate(topics_raw)
            ]

            # mini chart for top 3
            top_topics = [t["topic"] for t in trending_topics[:3]]
            chart_data = []
            if top_topics:
                cur.execute(
                    """
                    SELECT date, topic_name, mention_count
                    FROM trend_aggregations
                    WHERE date >= CURRENT_DATE - INTERVAL '1 day' * %s
                      AND topic_name = ANY(%s)
                    ORDER BY date ASC
                    """,
                    (days, top_topics),
                )
                date_map = {}
                for date, topic, count in cur.fetchall():
                    key = date.isoformat()
                    date_map.setdefault(key, {"time": key})
                    date_map[key][topic] = int(count)
                chart_data = list(date_map.values())

            # stats
            cur.execute(
                """
                SELECT COUNT(DISTINCT tweet_id), COUNT(DISTINCT topic_name)
                FROM topics
                WHERE mentioned_at >= CURRENT_DATE - INTERVAL '30 days'
                """
            )
            total_tweets, active_topics = cur.fetchone()

            cur.execute(
                """
                SELECT EXTRACT(HOUR FROM mentioned_at)::INT AS hour, COUNT(*) AS count
                FROM topics
                WHERE mentioned_at >= CURRENT_DATE - INTERVAL '7 days'
                GROUP BY hour
                ORDER BY count DESC
                LIMIT 1
                """
            )
            peak = cur.fetchone()
            peak_hour = f"{int(peak[0])}:00" if peak else "N/A"

            cur.execute(
                """
                SELECT AVG(growth_rate)
                FROM trend_aggregations
                WHERE date >= CURRENT_DATE - INTERVAL '7 days'
                """
            )
            avg_growth_row = cur.fetchone()
            avg_growth = round(float(avg_growth_row[0] or 0), 1) if avg_growth_row else 0

        return {
            "trending_topics": trending_topics,
            "chart_data": chart_data,
            "stats": {
                "total_queries": f"{(total_tweets or 0):,}",
                "active_topics": int(active_topics or 0),
                "peak_hour": peak_hour,
                "avg_growth": f"+{avg_growth}%" if avg_growth >= 0 else f"{avg_growth}%",
            },
            "metadata": {
                "days": days,
                "category": category or "all",
                "generated_at": datetime.utcnow().isoformat() + "Z",
            },
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {e}")
    finally:
        put_conn(conn)

@app.get("/api/topics/search")
def search_topics(q: str = Query(..., min_length=2), limit: int = Query(10, ge=1, le=50)):
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT topic_name, category, COUNT(*) AS mentions
                FROM topics
                WHERE topic_name ILIKE %s
                GROUP BY topic_name, category
                ORDER BY mentions DESC
                LIMIT %s
                """,
                (f"%{q}%", limit),
            )
            rows = cur.fetchall()
        return {"results": [{"topic": t, "category": c, "mentions": int(m)} for t, c, m in rows]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        put_conn(conn)

@app.get("/api/stats")
def get_stats():
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) FROM raw_tweets")
            total_tweets = cur.fetchone()[0] or 0

            cur.execute("SELECT COUNT(DISTINCT topic_name) FROM topics")
            total_topics = cur.fetchone()[0] or 0

            cur.execute(
                """
                SELECT COALESCE(SUM(posts_pulled), 0)
                FROM api_usage
                WHERE query_date >= DATE_TRUNC('month', CURRENT_DATE)
                """
            )
            month_collected = cur.fetchone()[0] or 0

            cur.execute("SELECT MIN(created_at) FROM raw_tweets")
            started = cur.fetchone()[0]

        return {
            "total_tweets": int(total_tweets),
            "total_topics": int(total_topics),
            "month_collected": int(month_collected),
            "collection_started": started.isoformat() if started else None,
            "days_active": (datetime.utcnow() - started).days if started else 0,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        put_conn(conn)

@app.get("/api/categories")
def get_categories():
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT category,
                       COUNT(DISTINCT topic_name) AS topic_count,
                       SUM(mention_count)         AS total_mentions
                FROM trend_aggregations
                WHERE date >= CURRENT_DATE - INTERVAL '7 days'
                GROUP BY category
                ORDER BY total_mentions DESC NULLS LAST
                """
            )
            rows = cur.fetchall()
        return {
            "categories": [
                {
                    "id": cat,
                    "name": (cat or "").capitalize(),
                    "topic_count": int(tc or 0),
                    "mentions": int(m or 0),
                }
                for cat, tc, m in rows
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        put_conn(conn)

@app.get("/api/interest")
def interest_over_time(
        topics: List[str] = Query(..., description="One or more topic names"),
        hours: int = Query(48, ge=1, le=720, description="Window in hours"),
        metric: str = Query("weighted", pattern="^(weighted|mentions)$"),
):
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            sql = f"""
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
                SELECT ta.bucket_ts, ta.topic_name, ta.category,
                       ta.{ 'weighted' if metric=='weighted' else 'mentions' } AS v
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
                   CASE WHEN m.vmax > 0
                        THEN ROUND(100.0 * j.v / m.vmax)::INT
                        ELSE 0
                   END AS index_0_100
            FROM joined j
            JOIN maxes m USING (topic_name, category)
            ORDER BY j.bucket_ts ASC, j.topic_name ASC
            """
            cur.execute(sql, (hours, topics))
            rows = cur.fetchall()

        out = {}
        for ts, topic, cat, idx in rows:
            key = ts.replace(tzinfo=None).isoformat() + "Z"
            out.setdefault(key, {"time": key})
            out[key][topic] = idx

        return {"metric": metric, "hours": hours, "topics": topics, "series": list(out.values())}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Interest API error: {e}")
    finally:
        put_conn(conn)

# ---------- Interest signups ----------
class InterestSignup(BaseModel):
    email: EmailStr

@app.post("/api/interest-signup")
def signup_interest(signup: InterestSignup):
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO interest_signups (email)
                VALUES (%s)
                ON CONFLICT (email) DO NOTHING
                RETURNING id
                """,
                (signup.email,),
            )
            inserted = cur.fetchone()

            cur.execute("SELECT COUNT(*) FROM interest_signups")
            total = int(cur.fetchone()[0] or 0)

        conn.commit()
        if inserted:
            msg = "Thanks for your interest! We'll notify you when we launch."
        else:
            msg = "You're already on the list!"
        return {"success": True, "message": msg, "total_signups": total}
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        put_conn(conn)

@app.get("/api/interest-count")
def get_interest_count():
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) FROM interest_signups")
            count = int(cur.fetchone()[0] or 0)
        return {"count": count}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        put_conn(conn)

# Local dev runner (use Gunicorn in prod)
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="0.0.0.0", port=int(os.getenv("PORT", "8000")), reload=True)
