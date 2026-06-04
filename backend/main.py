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
import io
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# pyrefly: ignore [missing-import]
import uvicorn
# pyrefly: ignore [missing-import]
import sentry_sdk
# pyrefly: ignore [missing-import]
from sentry_sdk.integrations.fastapi import FastAPIIntegration
# pyrefly: ignore [missing-import]
from fastapi import FastAPI, HTTPException, BackgroundTasks, Request
# pyrefly: ignore [missing-import]
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles # pyrefly: ignore [missing-import]
from fastapi.responses import JSONResponse, FileResponse, RedirectResponse # pyrefly: ignore [missing-import]
# pyrefly: ignore [missing-import]
from pydantic import BaseModel
# pyrefly: ignore [missing-import]
from apscheduler.schedulers.asyncio import AsyncIOScheduler
# pyrefly: ignore [missing-import]
from apscheduler.triggers.cron import CronTrigger
# pyrefly: ignore [missing-import]
from prometheus_fastapi_instrumentator import Instrumentator

from config import settings
from database import (
    init_db, save_post, update_post_status, get_posts,
    add_log, get_logs, get_analytics_summary,
    add_audit_log, get_audit_logs, save_config_key, get_all_configs
)
from news_agent import research_top_news
from content_engine import generate_all_posts
from carousel_generator import generate_all_carousels
from instagram_publisher import publisher
from redis_service import redis_service
from cloudinary_service import cloudinary_service

# ── Sentry Error Tracking ─────────────────────────────────────────────────────
if settings.SENTRY_DSN:
    try:
        sentry_sdk.init(
            dsn=settings.SENTRY_DSN,
            integrations=[FastAPIIntegration()],
            traces_sample_rate=1.0,
            profiles_sample_rate=1.0,
        )
        print("[Sentry] SDK monitoring active.")
    except Exception as e:
        print(f"[Sentry] Failed to initialize: {e}")

# ── App Lifespan Handler ──────────────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler"""
    # Startup
    print("[*] AI Instagram Automation System Starting...")
    
    # Initialize Neon PostgreSQL schemas
    try:
        init_db()
        print("[*] Database tables initialized successfully.")
    except Exception as e:
        print(f"[Fatal] Database schema generation failed: {e}")
        # Continue so container doesn't loop crash, letting healthz show error

    # Load dynamic overrides from config_store table
    try:
        configs = get_all_configs()
        settings.load_db_overrides(configs)
        print("[*] Configuration overrides loaded from database.")
    except Exception as e:
        print(f"[Config] Failed to load overrides: {e}")

    # Set up and start cron jobs
    _reschedule_jobs()
    scheduler.start()
    
    add_audit_log(
        actor="system",
        action="startup",
        status="success",
        details="System started. Scheduler active."
    )
    log_event("System started. Scheduler active.", "info")
    print(f"[*] Server ready at http://{settings.HOST}:{settings.PORT}")
    yield
    # Shutdown
    scheduler.shutdown()
    add_audit_log(
        actor="system",
        action="shutdown",
        status="success",
        details="System shut down cleanly."
    )
    print("[*] System stopped.")


app = FastAPI(title="AI Instagram Automation API", version="2.0.0", lifespan=lifespan)

# Allow CORS for Vercel frontends
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve generated local images
BASE_DIR = Path(__file__).resolve().parent.parent
OUTPUT_DIR = BASE_DIR / "output"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
app.mount("/output", StaticFiles(directory=str(OUTPUT_DIR)), name="output")

# Serve frontend production bundle if exists
FRONTEND_DIR = BASE_DIR / "frontend" / "dist"
if FRONTEND_DIR.exists():
    app.mount("/app", StaticFiles(directory=str(FRONTEND_DIR), html=True), name="frontend")

# ── Global State & Scheduler ──────────────────────────────────────────────────
scheduler = AsyncIOScheduler(timezone="Asia/Kolkata")
pipeline_running = False
pipeline_logs: List[str] = []
latest_news: List[dict] = []

# ── Prometheus Instrumentation ────────────────────────────────────────────────
if settings.ENABLE_METRICS:
    try:
        Instrumentator().instrument(app).expose(app, endpoint="/metrics")
        print("[Prometheus] Endpoint active under /metrics")
    except Exception as e:
        print(f"[Prometheus] Instrumentator error: {e}")

# ── Utility Logging ───────────────────────────────────────────────────────────
def log_event(msg: str, level: str = "info"):
    """Log an event to stdout, in-memory list, DB run logs, and Redis list"""
    ts = datetime.now().strftime("%H:%M:%S")
    entry = f"[{ts}] {msg}"
    
    # Store in-memory
    pipeline_logs.append(entry)
    if len(pipeline_logs) > 200:
        pipeline_logs.pop(0)

    # Store in Upstash Redis stream
    redis_service.push_log(f"{datetime.now().isoformat()} | {level.upper()} | {msg}")

    # Store in PostgreSQL log
    run_date = datetime.now().strftime("%Y-%m-%d")
    try:
        add_log(run_date, "pipeline", msg, level)
    except Exception as e:
        print(f"[DB] Error writing run_log: {e}")

    print(f"[Pipeline] {msg}")


# ── Pipeline Logic ────────────────────────────────────────────────────────────
async def run_research_pipeline():
    """8:00 AM job — Research AI news and generate carousel content"""
    global pipeline_running, latest_news
    if pipeline_running:
        log_event("Pipeline already running, skipping", "warning")
        return

    # Distributed locking via Redis to support clustered backend nodes
    with redis_service.acquire_lock("research_pipeline", expire_seconds=1800) as acquired:
        if not acquired:
            log_event("Research execution blocked: Another node is running the pipeline.", "warning")
            return

        pipeline_running = True
        run_date = datetime.now().strftime("%Y-%m-%d")
        add_audit_log(actor="system", action="run_research_pipeline", status="success")

        try:
            log_event("🚀 Starting daily AI news research pipeline...")

            # Phase 1: Research
            log_event("📡 Phase 1: Researching latest AI news...")
            # Attempt to pull from Redis cache first to be nice to RSS feeds
            cached = redis_service.get_cached_news()
            if cached:
                articles = cached
                log_event("✓ Pulled news from Redis cache")
            else:
                articles = research_top_news(log_fn=log_event)
                redis_service.cache_news(articles, expire_seconds=7200)
            
            latest_news = articles
            log_event(f"✓ Found {len(articles)} top AI news articles")

            if not articles:
                log_event("⚠ No news articles found. Pipeline aborting.", "warning")
                return

            # Phase 2: Generate content
            log_event("🤖 Phase 2: Generating AI carousel content...")
            posts = generate_all_posts(articles, log_fn=log_event)
            log_event(f"✓ Generated content for {len(posts)} posts")

            # Phase 3: Generate carousel images
            log_event("🎨 Phase 3: Rendering carousel slides...")
            all_image_paths = generate_all_carousels(posts, run_date, log_fn=log_event)
            log_event(f"✓ Generated {sum(len(p) for p in all_image_paths)} carousel slides")

            # Phase 3.5: Upload assets to Cloudinary (Production Storage)
            log_event("☁️ Phase 3.5: Uploading generated slides to Cloudinary...")
            all_image_urls = []
            for i, paths in enumerate(all_image_paths, 1):
                urls = cloudinary_service.upload_carousel_post(run_date, i, paths)
                all_image_urls.append(urls)
                log_event(f"  ✓ Carousel {i} uploaded to Cloudinary: {len(urls)} slides secured")

            # Phase 4: Save to database
            log_event("💾 Phase 4: Saving posts to database...")
            for i, (post, image_paths, image_urls) in enumerate(zip(posts, all_image_paths, all_image_urls)):
                article = post["article"]
                content = post["content"]

                caption = content.get("caption", "")
                hashtags = content.get("hashtags", [])
                hashtag_str = " ".join(f"#{h.strip('#')}" for h in hashtags)
                full_caption = f"{caption}\n\n{hashtag_str}"

                slide_texts = {k: v for k, v in content.items() if k.startswith("slide")}

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
                    image_urls=image_urls
                )

            log_event("✅ Research pipeline complete! Posts queued for 9:00 AM publishing.")

        except Exception as e:
            import traceback
            error_detail = traceback.format_exc()
            log_event(f"❌ Pipeline error: {e}", "error")
            log_event(error_detail, "error")
            add_audit_log(actor="system", action="run_research_pipeline", status="failure", details=str(e))
        finally:
            pipeline_running = False


async def run_publish_pipeline():
    """9:00 AM job — Publish all queued posts to Instagram"""
    with redis_service.acquire_lock("publish_pipeline", expire_seconds=900) as acquired:
        if not acquired:
            log_event("Publishing blocked: Another node is publishing today's posts.", "warning")
            return

        run_date = datetime.now().strftime("%Y-%m-%d")
        log_event("📤 Starting Instagram publishing pipeline...")
        add_audit_log(actor="system", action="run_publish_pipeline", status="success")

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

            # instagrapi uses local paths for uploads
            ig_id = publisher.publish_carousel(
                image_paths=image_paths,
                caption=caption,
                post_id=post["id"],
                run_date=run_date,
            )

            if ig_id:
                log_event(f"✅ Post {i + 1} published! Instagram ID: {ig_id}", "success")
                add_audit_log(actor="system", action="publish_post", status="success", details=f"Post ID: {post['id']}, IG ID: {ig_id}")
            else:
                log_event(f"❌ Post {i + 1} failed to publish", "error")
                add_audit_log(actor="system", action="publish_post", status="failure", details=f"Post ID: {post['id']}")

            # Delay between posts (Instagram safety rate limit throttling)
            if i < len(queued) - 1:
                log_event("Waiting 30 seconds before next post...")
                await asyncio.sleep(30)

        log_event("📊 Publishing pipeline complete!")


# ── API Routes ────────────────────────────────────────────────────────────────

@app.get("/")
async def root():
    return RedirectResponse(url="/app/")


@app.get("/healthz")
async def health_check():
    """Liveness probe validating connection to Neon PostgreSQL and Upstash Redis"""
    postgres_ok = False
    redis_ok = False
    details = {}

    # Test Postgres (SQLAlchemy Pool)
    try:
        # pyrefly: ignore [missing-import]
        from sqlalchemy.sql import text
        from database import engine
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        postgres_ok = True
        details["postgres"] = "healthy"
    except Exception as e:
        details["postgres"] = f"unhealthy: {e}"

    # Test Redis (Ping)
    try:
        if redis_service.is_connected():
            redis_ok = True
            details["redis"] = "healthy"
        else:
            details["redis"] = "unhealthy: ping failed"
    except Exception as e:
        details["redis"] = f"unhealthy: {e}"

    status_code = 200 if (postgres_ok and redis_ok) else 503
    return JSONResponse(
        status_code=status_code,
        content={
            "status": "healthy" if status_code == 200 else "unhealthy",
            "timestamp": datetime.utcnow().isoformat(),
            **details
        }
    )


@app.get("/api/status")
async def get_status():
    data = {
        "status": "running",
        "pipeline_active": pipeline_running,
        "instagram_configured": bool(settings.INSTAGRAM_USERNAME and settings.INSTAGRAM_PASSWORD),
        "gemini_configured": bool(settings.GEMINI_API_KEY),
        "newsapi_configured": bool(settings.NEWS_API_KEY),
        "cloudinary_configured": cloudinary_service.configured,
        "redis_configured": redis_service.is_connected(),
        "schedule": {
            "research": f"{settings.RESEARCH_HOUR:02d}:{settings.RESEARCH_MINUTE:02d}",
            "publish": f"{settings.PUBLISH_HOUR:02d}:{settings.PUBLISH_MINUTE:02d}",
        },
        "server_time": datetime.now().isoformat(),
        "log_count": len(pipeline_logs),
    }
    return {"success": True, "data": data}


@app.get("/api/news")
async def get_news():
    # Attempt to read cached news
    news = redis_service.get_cached_news()
    if not news:
        news = latest_news
    return {"success": True, "data": news}


@app.get("/api/posts")
async def get_posts_api(date: Optional[str] = None, limit: int = 20):
    posts = get_posts(run_date=date, limit=limit)
    
    # Process image URLs
    for post in posts:
        # Check if Cloudinary URLs are stored
        if post.get("image_urls") and len(post["image_urls"]) > 0:
            post["image_urls"] = post["image_urls"]
        else:
            # Fallback to local files
            post["image_urls"] = [
                f"/output/{Path(p).relative_to(OUTPUT_DIR).as_posix()}"
                for p in post.get("image_paths", [])
                if Path(p).exists()
            ]
    return {"success": True, "posts": posts, "total": len(posts)}


@app.get("/api/logs")
async def get_logs_api(limit: int = 100):
    # Retrieve logs stream from Upstash Redis
    redis_logs = redis_service.get_logs(limit)
    live_logs = []
    
    for rl in redis_logs:
        try:
            parts = rl.split(" | ", 2)
            if len(parts) == 3:
                # Format: [time] message
                dt = datetime.fromisoformat(parts[0])
                live_logs.append(f"[{dt.strftime('%H:%M:%S')}] {parts[2]}")
            else:
                live_logs.append(rl)
        except Exception:
            live_logs.append(rl)

    # Fallback to backend instance in-memory list
    if not live_logs:
        live_logs = pipeline_logs[-50:]

    db_logs = get_logs(limit=limit)
    return {
        "success": True,
        "logs": live_logs,
        "db_logs": db_logs,
    }


@app.get("/api/audit-logs")
async def get_audit_logs_api(limit: int = 100):
    """Retrieve audit logs for admin panel"""
    try:
        logs = get_audit_logs(limit)
        return {"success": True, "data": logs}
    except Exception as e:
        return JSONResponse(status_code=500, content={"success": False, "error": str(e)})


@app.post("/api/run-research")
async def trigger_research(background_tasks: BackgroundTasks, request: Request):
    """Manually trigger the research pipeline"""
    if pipeline_running:
        raise HTTPException(status_code=409, detail="Pipeline already running")
        
    add_audit_log(
        actor="admin_user",
        action="manual_research_trigger",
        status="success",
        ip_address=request.client.host if request.client else None
    )
    background_tasks.add_task(run_research_pipeline)
    return {"success": True, "message": "Research pipeline started", "status": "started"}


@app.post("/api/run-publish")
async def trigger_publish(background_tasks: BackgroundTasks, request: Request):
    """Manually trigger publishing for today's posts"""
    add_audit_log(
        actor="admin_user",
        action="manual_publish_trigger",
        status="success",
        ip_address=request.client.host if request.client else None
    )
    background_tasks.add_task(run_publish_pipeline)
    return {"success": True, "message": "Publishing pipeline started", "status": "started"}


@app.post("/api/run-all")
async def trigger_full_pipeline(background_tasks: BackgroundTasks, request: Request):
    """Run research + generate + publish immediately"""
    async def full_run():
        await run_research_pipeline()
        log_event("Waiting 30 seconds before publishing...")
        await asyncio.sleep(30)
        await run_publish_pipeline()

    if pipeline_running:
        raise HTTPException(status_code=409, detail="Pipeline already running")
        
    add_audit_log(
        actor="admin_user",
        action="manual_full_pipeline_trigger",
        status="success",
        ip_address=request.client.host if request.client else None
    )
    background_tasks.add_task(full_run)
    return {"success": True, "message": "Full pipeline started (research → publish)", "status": "started"}


@app.post("/api/publish/{post_id}")
async def publish_single(post_id: int, background_tasks: BackgroundTasks, request: Request):
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
            add_audit_log(
                actor="admin_user",
                action="manual_publish_single",
                status="success",
                details=f"Post ID: {post_id}, Instagram ID: {ig_id}",
                ip_address=request.client.host if request.client else None
            )
        else:
            log_event("❌ Manual publish failed", "error")
            add_audit_log(
                actor="admin_user",
                action="manual_publish_single",
                status="failure",
                details=f"Post ID: {post_id}",
                ip_address=request.client.host if request.client else None
            )

    background_tasks.add_task(do_publish)
    return {"success": True, "message": f"Publishing post {post_id}...", "status": "started"}


@app.get("/api/analytics")
async def get_analytics():
    summary = get_analytics_summary()
    return {"success": True, "data": summary}


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
async def update_config(config: ConfigUpdate, request: Request):
    """Update system configuration overrides stored in Postgres database"""
    updates = {}
    if config.instagram_username is not None:
        updates["instagram_username"] = config.instagram_username
    if config.instagram_password is not None:
        updates["instagram_password"] = config.instagram_password
    if config.gemini_api_key is not None:
        updates["gemini_api_key"] = config.gemini_api_key
    if config.news_api_key is not None:
        updates["news_api_key"] = config.news_api_key
    if config.research_hour is not None:
        updates["research_hour"] = config.research_hour
    if config.research_minute is not None:
        updates["research_minute"] = config.research_minute
    if config.publish_hour is not None:
        updates["publish_hour"] = config.publish_hour
    if config.publish_minute is not None:
        updates["publish_minute"] = config.publish_minute

    settings.update(save_config_key, **updates)
    _reschedule_jobs()
    
    # Audit log dynamic update
    masked = {k: ("***" if "key" in k or "password" in k else v) for k, v in updates.items()}
    add_audit_log(
        actor="admin_user",
        action="update_config",
        status="success",
        details=json.dumps(masked),
        ip_address=request.client.host if request.client else None
    )

    return {"success": True, "message": "Configuration updated successfully"}


@app.get("/api/config")
async def get_config():
    """Get current config (masked passwords and keys)"""
    config_data = {
        "instagram_username": settings.INSTAGRAM_USERNAME,
        "instagram_password": "***" if settings.INSTAGRAM_PASSWORD else "",
        "gemini_api_key": "***" if settings.GEMINI_API_KEY else "",
        "news_api_key": "***" if settings.NEWS_API_KEY else "",
        "research_hour": settings.RESEARCH_HOUR,
        "research_minute": settings.RESEARCH_MINUTE,
        "publish_hour": settings.PUBLISH_HOUR,
        "publish_minute": settings.PUBLISH_MINUTE,
    }
    return {"success": True, "data": config_data}


@app.post("/api/test-instagram")
async def test_instagram(request: Request):
    """Test Instagram credentials"""
    result = publisher.test_connection()
    status = "success" if result.get("success") else "failure"
    add_audit_log(
        actor="admin_user",
        action="test_instagram_connection",
        status=status,
        details=result.get("error", "Instagram verified"),
        ip_address=request.client.host if request.client else None
    )
    return {"success": result.get("success", False), "data": result}


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

    # Publish job (9:00 AM IST by default)
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
    return {"success": True, "data": jobs}


# ── Entry Point ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=False,
        log_level="info",
    )
