import os, psycopg2
from datetime import datetime
from typing import List, Optional
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(title="Grok Trends API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://localhost:3000",
        "https://grok-trends.vercel.app",  # Add your actual Vercel URL
        "https://groktrends.com"    # If you have one
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def get_db():
    return psycopg2.connect(
        host=os.getenv('PGHOST'),
        database=os.getenv('PGDATABASE'),
        user=os.getenv('PGUSER'),
        password=os.getenv('PGPASSWORD'),
        port=os.getenv('PGPORT', '5432')
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
            "/health": "Health check"
        }
    }

@app.get("/health")
def health_check():
    try:
        conn = get_db()
        cur = conn.cursor()
        cur.execute("SELECT 1")
        cur.close()
        conn.close()
        return {"status": "healthy", "database": "connected"}
    except Exception as e:
        return {"status": "unhealthy", "error": str(e)}

@app.get("/api/trends")
def get_trends(
        days: int = Query(7, ge=1, le=90),
        category: Optional[str] = Query(None),
        limit: int = Query(20, ge=1, le=100)
):
    try:
        conn = get_db()
        cur = conn.cursor()

        category_filter = ""
        params = [days, limit]
        if category and category != "all":
            category_filter = "AND category = %s"
            params.insert(1, category)

        cur.execute(f"""
            SELECT topic_name, category, SUM(mention_count) as total_mentions, AVG(growth_rate) as avg_growth
            FROM trend_aggregations
            WHERE date >= CURRENT_DATE - INTERVAL '%s days'
            {category_filter}
            GROUP BY topic_name, category
            ORDER BY total_mentions DESC, avg_growth DESC
            LIMIT %s
        """, params)
        topics_raw = cur.fetchall()

        trending_topics = []
        for idx, (topic, cat, mentions, growth) in enumerate(topics_raw, 1):
            trending_topics.append({
                "topic": topic,
                "category": cat,
                "mentions": int(mentions),
                "growth": round(float(growth or 0), 1),
                "rank": idx
            })

        chart_data = []
        top_topics = [t["topic"] for t in trending_topics[:3]]
        if top_topics:
            cur.execute(f"""
                SELECT date, topic_name, mention_count
                FROM trend_aggregations
                WHERE date >= CURRENT_DATE - INTERVAL '%s days'
                  AND topic_name = ANY(%s)
                ORDER BY date ASC
            """, (days, top_topics))
            chart_raw = cur.fetchall()
            date_map = {}
            for date, topic, count in chart_raw:
                key = date.isoformat()
                if key not in date_map:
                    date_map[key] = {"time": key}
                date_map[key][topic] = int(count)
            chart_data = list(date_map.values())

        cur.execute("""
            SELECT COUNT(DISTINCT tweet_id), COUNT(DISTINCT topic_name)
            FROM topics
            WHERE mentioned_at >= CURRENT_DATE - INTERVAL '30 days'
        """)
        total_tweets, active_topics = cur.fetchone()

        cur.execute("""
            SELECT EXTRACT(HOUR FROM mentioned_at) as hour, COUNT(*) as count
            FROM topics
            WHERE mentioned_at >= CURRENT_DATE - INTERVAL '7 days'
            GROUP BY hour ORDER BY count DESC LIMIT 1
        """)
        peak_result = cur.fetchone()
        peak_hour = f"{int(peak_result[0])}:00" if peak_result else "N/A"

        cur.execute("""
            SELECT AVG(growth_rate)
            FROM trend_aggregations
            WHERE date >= CURRENT_DATE - INTERVAL '7 days'
        """)
        avg_growth_result = cur.fetchone()
        avg_growth = round(float(avg_growth_result[0] or 0), 1) if avg_growth_result else 0

        cur.close()
        conn.close()

        return {
            "trending_topics": trending_topics,
            "chart_data": chart_data,
            "stats": {
                "total_queries": f"{(total_tweets or 0):,}",
                "active_topics": int(active_topics or 0),
                "peak_hour": peak_hour,
                "avg_growth": f"+{avg_growth}%" if avg_growth >= 0 else f"{avg_growth}%"
            },
            "metadata": {
                "days": days,
                "category": category or "all",
                "generated_at": datetime.now().isoformat()
            }
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@app.get("/api/topics/search")
def search_topics(q: str = Query(..., min_length=2), limit: int = Query(10, ge=1, le=50)):
    try:
        conn = get_db()
        cur = conn.cursor()
        cur.execute("""
            SELECT topic_name, category, COUNT(*) as mentions
            FROM topics
            WHERE topic_name ILIKE %s
            GROUP BY topic_name, category
            ORDER BY mentions DESC
            LIMIT %s
        """, (f"%{q}%", limit))
        results = cur.fetchall()
        cur.close()
        conn.close()
        return {"results": [
            {"topic": t, "category": c, "mentions": int(m)} for t, c, m in results
        ]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/stats")
def get_stats():
    try:
        conn = get_db()
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM raw_tweets")
        total_tweets = cur.fetchone()[0]
        cur.execute("SELECT COUNT(DISTINCT topic_name) FROM topics")
        total_topics = cur.fetchone()[0]
        cur.execute("""
            SELECT COALESCE(SUM(posts_pulled), 0)
            FROM api_usage
            WHERE query_date >= DATE_TRUNC('month', CURRENT_DATE)
        """)
        month_collected = cur.fetchone()[0]
        cur.execute("SELECT MIN(created_at) FROM raw_tweets")
        started = cur.fetchone()[0]
        cur.close()
        conn.close()
        return {
            "total_tweets": int(total_tweets or 0),
            "total_topics": int(total_topics or 0),
            "month_collected": int(month_collected or 0),
            "collection_started": started.isoformat() if started else None,
            "days_active": (datetime.now() - started).days if started else 0
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/categories")
def get_categories():
    try:
        conn = get_db()
        cur = conn.cursor()
        cur.execute("""
            SELECT category, COUNT(DISTINCT topic_name) as topic_count, SUM(mention_count) as total_mentions
            FROM trend_aggregations
            WHERE date >= CURRENT_DATE - INTERVAL '7 days'
            GROUP BY category
            ORDER BY total_mentions DESC
        """)
        rows = cur.fetchall()
        cur.close()
        conn.close()
        return {"categories": [
            {"id": cat, "name": (cat or "").capitalize(), "topic_count": int(tc or 0), "mentions": int(m or 0)}
            for cat, tc, m in rows
        ]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/interest")
def interest_over_time(
        topics: List[str] = Query(..., description="One or more topic names"),
        hours: int = Query(48, ge=1, le=720, description="Window in hours"),
        metric: str = Query("weighted", pattern="^(weighted|mentions)$")
):
    try:
        conn = get_db()
        cur = conn.cursor()
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
            SELECT ta.bucket_ts, ta.topic_name, ta.category, ta.{ 'weighted' if metric=='weighted' else 'mentions' } AS v
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
        """
        cur.execute(sql, (hours, topics))
        rows = cur.fetchall()
        cur.close()
        conn.close()

        out = {}
        for ts, topic, cat, idx in rows:
            key = ts.replace(tzinfo=None).isoformat() + "Z"
            if key not in out: out[key] = {"time": key}
            out[key][topic] = idx

        return {"metric": metric, "hours": hours, "topics": topics, "series": list(out.values())}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Interest API error: {str(e)}")
from pydantic import BaseModel, EmailStr

class InterestSignup(BaseModel):
    email: EmailStr

@app.post("/api/interest-signup")
def signup_interest(signup: InterestSignup):
    """Collect email for interest in full product"""
    try:
        conn = get_db()
        cur = conn.cursor()

        cur.execute("""
            INSERT INTO interest_signups (email)
            VALUES (%s)
            ON CONFLICT (email) DO NOTHING
            RETURNING id
        """, (signup.email,))

        result = cur.fetchone()

        # Count total signups
        cur.execute("SELECT COUNT(*) FROM interest_signups")
        total = cur.fetchone()[0]

        conn.commit()
        cur.close()
        conn.close()

        if result:
            return {
                "success": True,
                "message": "Thanks for your interest! We'll notify you when we launch.",
                "total_signups": total
            }
        else:
            return {
                "success": True,
                "message": "You're already on the list!",
                "total_signups": total
            }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/interest-count")
def get_interest_count():
    """Get total number of interested users"""
    try:
        conn = get_db()
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM interest_signups")
        count = cur.fetchone()[0]
        cur.close()
        conn.close()
        return {"count": count}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
