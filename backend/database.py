"""
database.py — SQLite database setup and models
Provides local-first transactional storage.
"""
import sqlite3
import json
from datetime import datetime
from typing import List, Dict, Optional
from config import settings

def get_conn():
    """Get a database connection to SQLite"""
    conn = sqlite3.connect(str(settings.DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Initializes tables in SQLite"""
    conn = get_conn()
    c = conn.cursor()

    # Posts Table
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
            slide_texts TEXT,            -- JSON formatted text
            caption TEXT,
            hashtags TEXT,               -- JSON formatted tags
            image_paths TEXT,            -- JSON formatted local paths inside container
            image_urls TEXT,             -- JSON formatted local URL aliases
            status TEXT DEFAULT 'queued',
            instagram_post_id TEXT,
            published_at TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Analytics Table
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
            engagement_rate REAL DEFAULT 0.0,
            fetched_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(post_id) REFERENCES posts(id) ON DELETE CASCADE
        )
    """)

    # Run logs (Scheduler operations)
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

    # Audit logs (Security actions)
    c.execute("""
        CREATE TABLE IF NOT EXISTS audit_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT DEFAULT CURRENT_TIMESTAMP,
            actor TEXT NOT NULL,
            action TEXT NOT NULL,
            status TEXT NOT NULL,
            details TEXT,
            ip_address TEXT
        )
    """)

    # Dynamic Configs Table
    c.execute("""
        CREATE TABLE IF NOT EXISTS config_store (
            key TEXT PRIMARY KEY,
            value TEXT
        )
    """)

    conn.commit()
    conn.close()


# ── Post Operations ───────────────────────────────────────────────────────────

def save_post(run_date: str, rank: int, topic: str, headline: str, source: str, source_url: str,
              virality_score: float, slide_texts: dict, caption: str, hashtags: List[str],
              image_paths: List[str], image_urls: List[str] = None) -> int:
    """Save a generated post to SQLite"""
    conn = get_conn()
    c = conn.cursor()
    c.execute("""
        INSERT INTO posts (run_date, rank, topic, headline, source, source_url,
            virality_score, slide_texts, caption, hashtags, image_paths, image_urls, status)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)
    """, (
        run_date, rank, topic, headline, source, source_url,
        virality_score,
        json.dumps(slide_texts),
        caption,
        json.dumps(hashtags),
        json.dumps(image_paths),
        json.dumps(image_urls or []),
        "queued"
    ))
    post_id = c.lastrowid
    conn.commit()
    conn.close()
    return post_id


def update_post_status(post_id: int, status: str, instagram_post_id: str = None):
    """Update publication status of a post"""
    conn = get_conn()
    c = conn.cursor()
    if instagram_post_id:
        c.execute("""
            UPDATE posts SET status=?, instagram_post_id=?, published_at=?
            WHERE id=?
        """, (status, instagram_post_id, datetime.utcnow().isoformat(), post_id))
    else:
        c.execute("UPDATE posts SET status=? WHERE id=?", (status, post_id))
    conn.commit()
    conn.close()


def get_posts(run_date: str = None, limit: int = 20) -> List[dict]:
    """Retrieve posts, parsing JSON strings to native lists/dicts"""
    conn = get_conn()
    c = conn.cursor()
    if run_date:
        rows = c.execute("SELECT * FROM posts WHERE run_date=? ORDER BY rank", (run_date,)).fetchall()
    else:
        rows = c.execute("SELECT * FROM posts ORDER BY created_at DESC LIMIT ?", (limit,)).fetchall()
    conn.close()

    result = []
    for row in rows:
        d = dict(row)
        d["slide_texts"] = json.loads(d["slide_texts"] or "{}")
        d["hashtags"] = json.loads(d["hashtags"] or "[]")
        d["image_paths"] = json.loads(d["image_paths"] or "[]")
        d["image_urls"] = json.loads(d["image_urls"] or "[]")
        result.append(d)
    return result


# ── Run Logs Operations (APScheduler runtime messages) ───────────────────────

def add_log(run_date: str, phase: str, message: str, level: str = "info"):
    """Write scheduler operational log to database"""
    conn = get_conn()
    c = conn.cursor()
    c.execute("""
        INSERT INTO run_logs (run_date, phase, message, level)
        VALUES (?,?,?,?)
    """, (run_date, phase, message, level))
    conn.commit()
    conn.close()


def get_logs(run_date: str = None, limit: int = 100) -> List[dict]:
    """Retrieve pipeline run logs"""
    conn = get_conn()
    c = conn.cursor()
    if run_date:
        rows = c.execute("""
            SELECT * FROM run_logs WHERE run_date=? ORDER BY created_at DESC LIMIT ?
        """, (run_date, limit)).fetchall()
    else:
        rows = c.execute("SELECT * FROM run_logs ORDER BY created_at DESC LIMIT ?", (limit,)).fetchall()
    conn.close()
    return [dict(row) for row in rows]


# ── Audit Logs Operations (Security / Admin Events) ──────────────────────────

def add_audit_log(actor: str, action: str, status: str, details: str = None, ip_address: str = None):
    """Write security or administrative action to the audit logs"""
    conn = get_conn()
    c = conn.cursor()
    try:
        c.execute("""
            INSERT INTO audit_logs (actor, action, status, details, ip_address)
            VALUES (?,?,?,?,?)
        """, (actor, action, status, details, ip_address))
        conn.commit()
    except Exception as e:
        print(f"[AuditDB] Failed to save audit log: {e}")
    finally:
        conn.close()


def get_audit_logs(limit: int = 100) -> List[dict]:
    """Retrieve system administrative audit logs"""
    conn = get_conn()
    c = conn.cursor()
    rows = c.execute("SELECT * FROM audit_logs ORDER BY timestamp DESC LIMIT ?", (limit,)).fetchall()
    conn.close()
    return [dict(row) for row in rows]


# ── Analytics Operations ──────────────────────────────────────────────────────

def save_analytics(post_id: int, likes: int, comments: int, shares: int, saves: int, reach: int, impressions: int):
    """Save parsed Instagram engagement data"""
    engagement_rate = 0.0
    if reach > 0:
        engagement_rate = round((likes + comments + saves) / reach * 100, 2)

    conn = get_conn()
    c = conn.cursor()
    c.execute("""
        INSERT INTO analytics (post_id, likes, comments, shares, saves, reach, impressions, engagement_rate)
        VALUES (?,?,?,?,?,?,?,?)
    """, (post_id, likes, comments, shares, saves, reach, impressions, engagement_rate))
    conn.commit()
    conn.close()


def get_analytics_summary() -> List[dict]:
    """Get analytics combined with post title and run dates"""
    conn = get_conn()
    c = conn.cursor()
    rows = c.execute("""
        SELECT a.likes, a.comments, a.saves, a.reach, a.engagement_rate, a.fetched_at,
               p.run_date, p.headline
        FROM analytics a JOIN posts p ON a.post_id = p.id
        ORDER BY a.fetched_at DESC LIMIT 50
    """).fetchall()
    conn.close()
    return [dict(row) for row in rows]


# ── Configuration Overrides Operations ────────────────────────────────────────

def save_config_key(key: str, value: str):
    """Save an override config key in database config_store"""
    conn = get_conn()
    c = conn.cursor()
    c.execute("""
        INSERT INTO config_store (key, value)
        VALUES (?, ?)
        ON CONFLICT(key) DO UPDATE SET value=excluded.value
    """, (key, value))
    conn.commit()
    conn.close()


def get_all_configs() -> dict:
    """Retrieve all configuration keys stored in SQLite"""
    conn = get_conn()
    c = conn.cursor()
    rows = c.execute("SELECT key, value FROM config_store").fetchall()
    conn.close()
    return {row["key"]: row["value"] for row in rows}
