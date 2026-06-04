"""
database.py — SQLite database setup and models
"""
import sqlite3
import json
from datetime import datetime
from pathlib import Path
from config import settings


def get_conn():
    conn = sqlite3.connect(str(settings.DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_conn()
    c = conn.cursor()

    c.execute("""
        CREATE TABLE IF NOT EXISTS posts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            run_date TEXT NOT NULL,
            rank INTEGER NOT NULL,
            topic TEXT,
            headline TEXT,
            source TEXT,
            source_url TEXT,
            virality_score REAL,
            slide_texts TEXT,
            caption TEXT,
            hashtags TEXT,
            image_paths TEXT,
            status TEXT DEFAULT 'queued',
            instagram_post_id TEXT,
            published_at TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS analytics (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            post_id INTEGER,
            likes INTEGER DEFAULT 0,
            comments INTEGER DEFAULT 0,
            shares INTEGER DEFAULT 0,
            saves INTEGER DEFAULT 0,
            reach INTEGER DEFAULT 0,
            impressions INTEGER DEFAULT 0,
            engagement_rate REAL DEFAULT 0,
            fetched_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(post_id) REFERENCES posts(id)
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS run_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            run_date TEXT NOT NULL,
            phase TEXT NOT NULL,
            message TEXT,
            level TEXT DEFAULT 'info',
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS config_store (
            key TEXT PRIMARY KEY,
            value TEXT
        )
    """)

    conn.commit()
    conn.close()


def save_post(run_date, rank, topic, headline, source, source_url,
              virality_score, slide_texts, caption, hashtags, image_paths):
    conn = get_conn()
    c = conn.cursor()
    c.execute("""
        INSERT INTO posts (run_date, rank, topic, headline, source, source_url,
            virality_score, slide_texts, caption, hashtags, image_paths, status)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?)
    """, (
        run_date, rank, topic, headline, source, source_url,
        virality_score,
        json.dumps(slide_texts),
        caption,
        json.dumps(hashtags),
        json.dumps(image_paths),
        "queued"
    ))
    post_id = c.lastrowid
    conn.commit()
    conn.close()
    return post_id


def update_post_status(post_id, status, instagram_post_id=None):
    conn = get_conn()
    c = conn.cursor()
    if instagram_post_id:
        c.execute("""UPDATE posts SET status=?, instagram_post_id=?, published_at=?
                     WHERE id=?""",
                  (status, instagram_post_id, datetime.utcnow().isoformat(), post_id))
    else:
        c.execute("UPDATE posts SET status=? WHERE id=?", (status, post_id))
    conn.commit()
    conn.close()


def get_posts(run_date=None, limit=20):
    conn = get_conn()
    c = conn.cursor()
    if run_date:
        rows = c.execute("SELECT * FROM posts WHERE run_date=? ORDER BY rank",
                         (run_date,)).fetchall()
    else:
        rows = c.execute("SELECT * FROM posts ORDER BY created_at DESC LIMIT ?",
                         (limit,)).fetchall()
    conn.close()
    result = []
    for row in rows:
        d = dict(row)
        d["slide_texts"] = json.loads(d["slide_texts"] or "[]")
        d["hashtags"] = json.loads(d["hashtags"] or "[]")
        d["image_paths"] = json.loads(d["image_paths"] or "[]")
        result.append(d)
    return result


def add_log(run_date, phase, message, level="info"):
    conn = get_conn()
    c = conn.cursor()
    c.execute("INSERT INTO run_logs (run_date, phase, message, level) VALUES (?,?,?,?)",
              (run_date, phase, message, level))
    conn.commit()
    conn.close()


def get_logs(run_date=None, limit=100):
    conn = get_conn()
    c = conn.cursor()
    if run_date:
        rows = c.execute(
            "SELECT * FROM run_logs WHERE run_date=? ORDER BY created_at DESC LIMIT ?",
            (run_date, limit)).fetchall()
    else:
        rows = c.execute(
            "SELECT * FROM run_logs ORDER BY created_at DESC LIMIT ?",
            (limit,)).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def save_analytics(post_id, likes, comments, shares, saves, reach, impressions):
    engagement_rate = 0
    if reach > 0:
        engagement_rate = round((likes + comments + saves) / reach * 100, 2)
    conn = get_conn()
    c = conn.cursor()
    c.execute("""INSERT INTO analytics
        (post_id, likes, comments, shares, saves, reach, impressions, engagement_rate)
        VALUES (?,?,?,?,?,?,?,?)""",
              (post_id, likes, comments, shares, saves, reach, impressions, engagement_rate))
    conn.commit()
    conn.close()


def get_analytics_summary():
    conn = get_conn()
    c = conn.cursor()
    rows = c.execute("""
        SELECT p.run_date, p.headline, a.likes, a.comments, a.saves, a.reach,
               a.engagement_rate, a.fetched_at
        FROM analytics a JOIN posts p ON a.post_id = p.id
        ORDER BY a.fetched_at DESC LIMIT 50
    """).fetchall()
    conn.close()
    return [dict(r) for r in rows]
