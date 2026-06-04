"""
database.py — Neon PostgreSQL database setup and SQLAlchemy models
"""
import json
from datetime import datetime
from typing import List, Dict, Optional
# pyrefly: ignore [missing-import]
from sqlalchemy import (
    create_engine, Column, Integer, String, Text, Float, DateTime, ForeignKey, desc
)
# pyrefly: ignore [missing-import]
from sqlalchemy.ext.declarative import declarative_base
# pyrefly: ignore [missing-import]
from sqlalchemy.orm import sessionmaker, relationship
from config import settings

# Create engine with connection pooling and pre-ping (liveness check)
engine = create_engine(
    settings.DATABASE_URL,
    pool_size=10,
    max_overflow=20,
    pool_recycle=1800,
    pool_pre_ping=True
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# ── SQLAlchemy Models ─────────────────────────────────────────────────────────

class Post(Base):
    __tablename__ = "posts"

    id = Column(Integer, primary key=True, index=True)
    run_date = Column(String(50), nullable=False, index=True)
    rank = Column(Integer, nullable=False)
    topic = Column(String(255))
    headline = Column(Text)
    source = Column(String(255))
    source_url = Column(Text)
    virality_score = Column(Float)
    slide_texts = Column(Text)  # JSON-encoded string
    caption = Column(Text)
    hashtags = Column(Text)     # JSON-encoded string
    image_paths = Column(Text)  # JSON-encoded string (local paths inside container)
    image_urls = Column(Text)   # JSON-encoded string (Cloudinary URLs)
    status = Column(String(50), default="queued")
    instagram_post_id = Column(String(100))
    published_at = Column(String(100))
    created_at = Column(DateTime, default=datetime.utcnow)

    analytics = relationship("Analytics", back_populates="post", cascade="all, delete-orphan")


class Analytics(Base):
    __tablename__ = "analytics"

    id = Column(Integer, primary key=True, index=True)
    post_id = Column(Integer, ForeignKey("posts.id", ondelete="CASCADE"), nullable=False)
    likes = Column(Integer, default=0)
    comments = Column(Integer, default=0)
    shares = Column(Integer, default=0)
    saves = Column(Integer, default=0)
    reach = Column(Integer, default=0)
    impressions = Column(Integer, default=0)
    engagement_rate = Column(Float, default=0.0)
    fetched_at = Column(DateTime, default=datetime.utcnow)

    post = relationship("Post", back_populates="analytics")


class RunLog(Base):
    __tablename__ = "run_logs"

    id = Column(Integer, primary key=True, index=True)
    run_date = Column(String(50), nullable=False, index=True)
    phase = Column(String(100), nullable=False)
    message = Column(Text)
    level = Column(String(50), default="info")
    created_at = Column(DateTime, default=datetime.utcnow)


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary key=True, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    actor = Column(String(100), nullable=False)        # e.g. "system", "user_admin"
    action = Column(String(100), nullable=False)       # e.g. "trigger_pipeline", "update_config"
    status = Column(String(50), nullable=False)        # e.g. "success", "failure"
    details = Column(Text)                             # JSON or description
    ip_address = Column(String(50), nullable=True)


class ConfigStore(Base):
    __tablename__ = "config_store"

    key = Column(String(100), primary key=True)
    value = Column(Text)


# ── Initialization & Helper Wrappers ──────────────────────────────────────────

def init_db():
    """Initializes tables in Neon PostgreSQL"""
    Base.metadata.create_all(bind=engine)


def get_db_session():
    """Returns a new DB session context manager"""
    session = SessionLocal()
    try:
        return session
    except Exception:
        session.close()
        raise


# ── Post Operations ───────────────────────────────────────────────────────────

def save_post(run_date: str, rank: int, topic: str, headline: str, source: str, source_url: str,
              virality_score: float, slide_texts: dict, caption: str, hashtags: List[str],
              image_paths: List[str], image_urls: List[str] = None) -> int:
    """Save a generated post to PostgreSQL"""
    session = SessionLocal()
    try:
        db_post = Post(
            run_date=run_date,
            rank=rank,
            topic=topic,
            headline=headline,
            source=source,
            source_url=source_url,
            virality_score=virality_score,
            slide_texts=json.dumps(slide_texts),
            caption=caption,
            hashtags=json.dumps(hashtags),
            image_paths=json.dumps(image_paths),
            image_urls=json.dumps(image_urls or []),
            status="queued"
        )
        session.add(db_post)
        session.commit()
        session.refresh(db_post)
        return db_post.id
    finally:
        session.close()


def update_post_status(post_id: int, status: str, instagram_post_id: str = None):
    """Update publication status of a post"""
    session = SessionLocal()
    try:
        post = session.query(Post).filter(Post.id == post_id).first()
        if post:
            post.status = status
            if instagram_post_id:
                post.instagram_post_id = instagram_post_id
                post.published_at = datetime.utcnow().isoformat()
            session.commit()
    finally:
        session.close()


def get_posts(run_date: str = None, limit: int = 20) -> List[dict]:
    """Retrieve posts, parsing JSON strings to native lists/dicts"""
    session = SessionLocal()
    try:
        query = session.query(Post)
        if run_date:
            posts = query.filter(Post.run_date == run_date).order_by(Post.rank).all()
        else:
            posts = query.order_by(desc(Post.created_at)).limit(limit).all()

        result = []
        for post in posts:
            p_dict = {
                "id": post.id,
                "run_date": post.run_date,
                "rank": post.rank,
                "topic": post.topic,
                "headline": post.headline,
                "source": post.source,
                "source_url": post.source_url,
                "virality_score": post.virality_score,
                "slide_texts": json.loads(post.slide_texts or "{}"),
                "caption": post.caption,
                "hashtags": json.loads(post.hashtags or "[]"),
                "image_paths": json.loads(post.image_paths or "[]"),
                "image_urls": json.loads(post.image_urls or "[]"),
                "status": post.status,
                "instagram_post_id": post.instagram_post_id,
                "published_at": post.published_at,
                "created_at": post.created_at.isoformat() if post.created_at else None
            }
            result.append(p_dict)
        return result
    finally:
        session.close()


# ── Run Logs Operations (APScheduler runtime messages) ───────────────────────

def add_log(run_date: str, phase: str, message: str, level: str = "info"):
    """Write scheduler operational log to database"""
    session = SessionLocal()
    try:
        log_entry = RunLog(
            run_date=run_date,
            phase=phase,
            message=message,
            level=level
        )
        session.add(log_entry)
        session.commit()
    finally:
        session.close()


def get_logs(run_date: str = None, limit: int = 100) -> List[dict]:
    """Retrieve pipeline run logs"""
    session = SessionLocal()
    try:
        query = session.query(RunLog)
        if run_date:
            logs = query.filter(RunLog.run_date == run_date).order_by(desc(RunLog.created_at)).limit(limit).all()
        else:
            logs = query.order_by(desc(RunLog.created_at)).limit(limit).all()

        return [
            {
                "id": log.id,
                "run_date": log.run_date,
                "phase": log.phase,
                "message": log.message,
                "level": log.level,
                "created_at": log.created_at.isoformat() if log.created_at else None
            }
            for log in logs
        ]
    finally:
        session.close()


# ── Audit Logs Operations (Security / Admin Events) ──────────────────────────

def add_audit_log(actor: str, action: str, status: str, details: str = None, ip_address: str = None):
    """Write security or administrative action to the audit logs"""
    session = SessionLocal()
    try:
        audit = AuditLog(
            actor=actor,
            action=action,
            status=status,
            details=details,
            ip_address=ip_address
        )
        session.add(audit)
        session.commit()
    except Exception as e:
        print(f"[AuditDB] Failed to save audit log: {e}")
    finally:
        session.close()


def get_audit_logs(limit: int = 100) -> List[dict]:
    """Retrieve system administrative audit logs"""
    session = SessionLocal()
    try:
        logs = session.query(AuditLog).order_by(desc(AuditLog.timestamp)).limit(limit).all()
        return [
            {
                "id": log.id,
                "timestamp": log.timestamp.isoformat() if log.timestamp else None,
                "actor": log.actor,
                "action": log.action,
                "status": log.status,
                "details": log.details,
                "ip_address": log.ip_address
            }
            for log in logs
        ]
    finally:
        session.close()


# ── Analytics Operations ──────────────────────────────────────────────────────

def save_analytics(post_id: int, likes: int, comments: int, shares: int, saves: int, reach: int, impressions: int):
    """Save parsed Instagram engagement data"""
    engagement_rate = 0.0
    if reach > 0:
        engagement_rate = round((likes + comments + saves) / reach * 100, 2)

    session = SessionLocal()
    try:
        anal = Analytics(
            post_id=post_id,
            likes=likes,
            comments=comments,
            shares=shares,
            saves=saves,
            reach=reach,
            impressions=impressions,
            engagement_rate=engagement_rate
        )
        session.add(anal)
        session.commit()
    finally:
        session.close()


def get_analytics_summary() -> List[dict]:
    """Get analytics combined with post title and run dates"""
    session = SessionLocal()
    try:
        results = session.query(
            Analytics.likes, Analytics.comments, Analytics.saves, Analytics.reach,
            Analytics.engagement_rate, Analytics.fetched_at,
            Post.run_date, Post.headline
        ).join(Post, Analytics.post_id == Post.id).order_by(desc(Analytics.fetched_at)).limit(50).all()

        return [
            {
                "likes": r.likes,
                "comments": r.comments,
                "saves": r.saves,
                "reach": r.reach,
                "engagement_rate": r.engagement_rate,
                "fetched_at": r.fetched_at.isoformat() if r.fetched_at else None,
                "run_date": r.run_date,
                "headline": r.headline
            }
            for r in results
        ]
    finally:
        session.close()


# ── Configuration Overrides Operations ────────────────────────────────────────

def save_config_key(key: str, value: str):
    """Save an override config key in database config_store"""
    session = SessionLocal()
    try:
        config = session.query(ConfigStore).filter(ConfigStore.key == key).first()
        if config:
            config.value = value
        else:
            config = ConfigStore(key=key, value=value)
            session.add(config)
        session.commit()
    finally:
        session.close()


def get_all_configs() -> dict:
    """Retrieve all configuration keys stored in PostgreSQL"""
    session = SessionLocal()
    try:
        configs = session.query(ConfigStore).all()
        return {config.key: config.value for config in configs}
    finally:
        session.close()
