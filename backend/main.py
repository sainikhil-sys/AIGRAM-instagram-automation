"""
main.py — FastAPI Server + APScheduler for AI Instagram Automation
Entry point for the backend system
"""
import asyncio
import json
import os
import sys
from contextlib import asynccontextmanager
from datetime import datetime
from pathlib import Path
from typing import List, Optional

# Fix Windows console Unicode output
import sys
import io
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

import uvicorn
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse, FileResponse
from pydantic import BaseModel
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.date import DateTrigger

from config import settings
from database import (
    init_db, save_post, update_post_status, get_posts,
    add_log, get_logs, get_analytics_summary
)
from news_agent import research_top_news
from content_engine import generate_all_posts
from carousel_generator import generate_all_carousels
from instagram_publisher import publisher

# ── App Init ──────────────────────────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler"""
    # Startup
    print("[*] AI Instagram Automation System Starting...")
    init_db()
    _reschedule_jobs()
    scheduler.start()
    log_event("System started. Scheduler active.", "info")
    print(f"[*] Server ready at http://{settings.HOST}:{settings.PORT}")
    print(f"[*] Dashboard: http://localhost:{settings.PORT}")
    yield
    # Shutdown
    scheduler.shutdown()
    print("[*] System stopped.")


app = FastAPI(title="AI Instagram Automation API", version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve generated images
BASE_DIR = Path(__file__).resolve().parent.parent
OUTPUT_DIR = BASE_DIR / "output"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

app.mount("/output", StaticFiles(directory=str(OUTPUT_DIR)), name="output")

# Serve frontend
FRONTEND_DIR = BASE_DIR / "frontend"
if FRONTEND_DIR.exists():
    app.mount("/app", StaticFiles(directory=str(FRONTEND_DIR), html=True), name="frontend")

# ── Global State ──────────────────────────────────────────────────────────────
scheduler = AsyncIOScheduler(timezone="Asia/Kolkata")
pipeline_running = False
pipeline_logs: List[str] = []
latest_news: List[dict] = []


# ── Pipeline ──────────────────────────────────────────────────────────────────
def log_event(msg: str, level: str = "info"):
    """Add to in-memory and DB log"""
    ts = datetime.now().strftime("%H:%M:%S")
    entry = f"[{ts}] {msg}"
    pipeline_logs.append(entry)
    if len(pipeline_logs) > 200:
        pipeline_logs.pop(0)
    run_date = datetime.now().strftime("%Y-%m-%d")
    add_log(run_date, "pipeline", msg, level)
    print(f"[Pipeline] {msg}")


async def run_research_pipeline():
    """8:00 AM job — Research AI news and generate carousel content"""
    global pipeline_running, latest_news
    if pipeline_running:
        log_event("Pipeline already running, skipping", "warning")
        return

    pipeline_running = True
    run_date = datetime.now().strftime("%Y-%m-%d")

    try:
        log_event("🚀 Starting daily AI news research pipeline...")

        # Phase 1: Research
        log_event("📡 Phase 1: Researching latest AI news...")
        articles = research_top_news(log_fn=log_event)
        latest_news = articles
        log_event(f"✓ Found {len(articles)} top AI news articles")

        # Phase 2: Generate content
        log_event("🤖 Phase 2: Generating AI carousel content...")
        posts = generate_all_posts(articles, log_fn=log_event)
        log_event(f"✓ Generated content for {len(posts)} posts")

        # Phase 3: Generate carousel images
        log_event("🎨 Phase 3: Rendering carousel slides...")
        all_image_paths = generate_all_carousels(posts, run_date, log_fn=log_event)
        log_event(f"✓ Generated {sum(len(p) for p in all_image_paths)} carousel slides")

        # Phase 4: Save to database
        log_event("💾 Phase 4: Saving posts to database...")
        for i, (post, image_paths) in enumerate(zip(posts, all_image_paths)):
            article = post["article"]
            content = post["content"]

            caption = content.get("caption", "")
            hashtags = content.get("hashtags", [])
            hashtag_str = " ".join(f"#{h.strip('#')}" for h in hashtags)
            full_caption = f"{caption}\n\n{hashtag_str}"

            slide_texts = {k: v for k, v in content.items()
                           if k.startswith("slide")}

            save_post(
                run_date=run_date,
                rank=i + 1,
                topic=article.get("source", ""),
                headline=article.get("title", ""),
                source=article.get("source", ""),
                source_url=article.get("url", ""),
                virality_score=article.get("score", 0),
                slide_texts=slide_texts,
                caption=full_caption,
                hashtags=hashtags,
                image_paths=image_paths,
            )

        log_event("✅ Research pipeline complete! Posts queued for 9:00 AM publishing.")

    except Exception as e:
        import traceback
        error_detail = traceback.format_exc()
        log_event(f"❌ Pipeline error: {e}", "error")
        log_event(error_detail, "error")
    finally:
        pipeline_running = False


async def run_publish_pipeline():
    """9:00 AM job — Publish all queued posts to Instagram"""
    run_date = datetime.now().strftime("%Y-%m-%d")
    log_event("📤 Starting Instagram publishing pipeline...")

    posts = get_posts(run_date=run_date)
    queued = [p for p in posts if p["status"] == "queued"]

    if not queued:
        log_event("No queued posts found for today. Run research first.", "warning")
        return

    log_event(f"Found {len(queued)} posts to publish")

    if not settings.INSTAGRAM_USERNAME or not settings.INSTAGRAM_PASSWORD:
        log_event("❌ Instagram credentials not configured. Set them in the dashboard.", "error")
        return

    for i, post in enumerate(queued):
        log_event(f"📸 Publishing post {i + 1}/{len(queued)}: {post['headline'][:50]}...")
        image_paths = post.get("image_paths", [])
        caption = post.get("caption", "")

        ig_id = publisher.publish_carousel(
            image_paths=image_paths,
            caption=caption,
            post_id=post["id"],
            run_date=run_date,
        )

        if ig_id:
            log_event(f"✅ Post {i + 1} published! Instagram ID: {ig_id}", "success")
        else:
            log_event(f"❌ Post {i + 1} failed to publish", "error")

        # Delay between posts (Instagram safety)
        if i < len(queued) - 1:
            log_event("Waiting 30 seconds before next post...")
            await asyncio.sleep(30)

    log_event("📊 Publishing pipeline complete!")


# ── API Routes ────────────────────────────────────────────────────────────────

@app.get("/")
async def root():
    return FileResponse(str(FRONTEND_DIR / "index.html"))


@app.get("/api/status")
async def get_status():
    return {
        "status": "running",
        "pipeline_active": pipeline_running,
        "instagram_configured": bool(settings.INSTAGRAM_USERNAME and settings.INSTAGRAM_PASSWORD),
        "gemini_configured": bool(settings.GEMINI_API_KEY),
        "newsapi_configured": bool(settings.NEWS_API_KEY),
        "schedule": {
            "research": f"{settings.RESEARCH_HOUR:02d}:{settings.RESEARCH_MINUTE:02d}",
            "publish": f"{settings.PUBLISH_HOUR:02d}:{settings.PUBLISH_MINUTE:02d}",
        },
        "server_time": datetime.now().isoformat(),
        "log_count": len(pipeline_logs),
    }


@app.get("/api/news")
async def get_news():
    return {"news": latest_news}


@app.get("/api/posts")
async def get_posts_api(date: Optional[str] = None, limit: int = 20):
    posts = get_posts(run_date=date, limit=limit)
    # Convert image paths to URLs
    for post in posts:
        post["image_urls"] = [
            f"/output/{Path(p).relative_to(OUTPUT_DIR).as_posix()}"
            for p in post.get("image_paths", [])
            if Path(p).exists()
        ]
    return {"posts": posts, "total": len(posts)}


@app.get("/api/logs")
async def get_logs_api(limit: int = 100):
    db_logs = get_logs(limit=limit)
    return {
        "live_logs": pipeline_logs[-50:],
        "db_logs": db_logs,
    }


@app.post("/api/run-research")
async def trigger_research(background_tasks: BackgroundTasks):
    """Manually trigger the research pipeline"""
    if pipeline_running:
        raise HTTPException(status_code=409, detail="Pipeline already running")
    background_tasks.add_task(run_research_pipeline)
    return {"message": "Research pipeline started", "status": "started"}


@app.post("/api/run-publish")
async def trigger_publish(background_tasks: BackgroundTasks):
    """Manually trigger publishing for today's posts"""
    background_tasks.add_task(run_publish_pipeline)
    return {"message": "Publishing pipeline started", "status": "started"}


@app.post("/api/run-all")
async def trigger_full_pipeline(background_tasks: BackgroundTasks):
    """Run research + generate + publish immediately"""
    async def full_run():
        await run_research_pipeline()
        log_event("Waiting 60 seconds before publishing...")
        await asyncio.sleep(60)
        await run_publish_pipeline()

    if pipeline_running:
        raise HTTPException(status_code=409, detail="Pipeline already running")
    background_tasks.add_task(full_run)
    return {"message": "Full pipeline started (research → publish)", "status": "started"}


@app.post("/api/publish/{post_id}")
async def publish_single(post_id: int, background_tasks: BackgroundTasks):
    """Manually publish a specific post"""
    posts = get_posts(limit=100)
    post = next((p for p in posts if p["id"] == post_id), None)
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")

    async def do_publish():
        ig_id = publisher.publish_carousel(
            image_paths=post["image_paths"],
            caption=post["caption"],
            post_id=post_id,
            run_date=datetime.now().strftime("%Y-%m-%d"),
        )
        if ig_id:
            log_event(f"✅ Manual publish successful! ID: {ig_id}")
        else:
            log_event("❌ Manual publish failed", "error")

    background_tasks.add_task(do_publish)
    return {"message": f"Publishing post {post_id}...", "status": "started"}


@app.get("/api/analytics")
async def get_analytics():
    summary = get_analytics_summary()
    return {"analytics": summary}


class ConfigUpdate(BaseModel):
    instagram_username: Optional[str] = None
    instagram_password: Optional[str] = None
    gemini_api_key: Optional[str] = None
    news_api_key: Optional[str] = None
    research_hour: Optional[int] = None
    research_minute: Optional[int] = None
    publish_hour: Optional[int] = None
    publish_minute: Optional[int] = None


@app.post("/api/config")
async def update_config(config: ConfigUpdate):
    """Update system configuration"""
    updates = {}
    if config.instagram_username is not None:
        updates["INSTAGRAM_USERNAME"] = config.instagram_username
    if config.instagram_password is not None:
        updates["INSTAGRAM_PASSWORD"] = config.instagram_password
    if config.gemini_api_key is not None:
        updates["GEMINI_API_KEY"] = config.gemini_api_key
    if config.news_api_key is not None:
        updates["NEWS_API_KEY"] = config.news_api_key
    if config.research_hour is not None:
        updates["RESEARCH_HOUR"] = config.research_hour
    if config.research_minute is not None:
        updates["RESEARCH_MINUTE"] = config.research_minute
    if config.publish_hour is not None:
        updates["PUBLISH_HOUR"] = config.publish_hour
    if config.publish_minute is not None:
        updates["PUBLISH_MINUTE"] = config.publish_minute

    settings.update(**updates)
    _reschedule_jobs()
    return {"message": "Configuration updated successfully"}


@app.get("/api/config")
async def get_config():
    """Get current config (masked passwords)"""
    return {
        "instagram_username": settings.INSTAGRAM_USERNAME,
        "instagram_password": "***" if settings.INSTAGRAM_PASSWORD else "",
        "gemini_api_key": "***" if settings.GEMINI_API_KEY else "",
        "news_api_key": "***" if settings.NEWS_API_KEY else "",
        "research_hour": settings.RESEARCH_HOUR,
        "research_minute": settings.RESEARCH_MINUTE,
        "publish_hour": settings.PUBLISH_HOUR,
        "publish_minute": settings.PUBLISH_MINUTE,
    }


@app.post("/api/test-instagram")
async def test_instagram():
    """Test Instagram connection"""
    result = publisher.test_connection()
    return result


# ── Scheduler Setup ───────────────────────────────────────────────────────────
def _reschedule_jobs():
    """Reschedule jobs with current settings"""
    for job in scheduler.get_jobs():
        job.remove()

    # Research job (8:00 AM IST by default)
    scheduler.add_job(
        run_research_pipeline,
        CronTrigger(
            hour=settings.RESEARCH_HOUR,
            minute=settings.RESEARCH_MINUTE,
            timezone="Asia/Kolkata"
        ),
        id="research",
        name="Daily AI News Research",
        replace_existing=True,
    )

    # Publish job (9:00 AM IST)
    scheduler.add_job(
        run_publish_pipeline,
        CronTrigger(
            hour=settings.PUBLISH_HOUR,
            minute=settings.PUBLISH_MINUTE,
            timezone="Asia/Kolkata"
        ),
        id="publish",
        name="Daily Instagram Publishing",
        replace_existing=True,
    )

    print(f"[Scheduler] Research: {settings.RESEARCH_HOUR:02d}:{settings.RESEARCH_MINUTE:02d} IST")
    print(f"[Scheduler] Publish:  {settings.PUBLISH_HOUR:02d}:{settings.PUBLISH_MINUTE:02d} IST")


@app.get("/api/schedule")
async def get_schedule():
    """Get scheduled jobs"""
    jobs = []
    for job in scheduler.get_jobs():
        next_run = job.next_run_time
        jobs.append({
            "id": job.id,
            "name": job.name,
            "next_run": next_run.isoformat() if next_run else None,
        })
    return {"jobs": jobs}


# ── Entry Point ───────────────────────────────────────────────────────────────
if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=False,
        log_level="info",
    )
