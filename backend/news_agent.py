"""
news_agent.py — AI News Research Engine
Monitors RSS feeds, NewsAPI, Reddit, and Product Hunt
Returns top 5 scored AI news items
"""
import feedparser
import requests
import json
import time
import re
from datetime import datetime, timedelta
from typing import List, Dict
from config import settings

# ── RSS Feed Sources ──────────────────────────────────────────────────────────
RSS_FEEDS = [
    {"name": "OpenAI Blog",       "url": "https://openai.com/blog/rss.xml"},
    {"name": "Google DeepMind",   "url": "https://deepmind.google/blog/rss.xml"},
    {"name": "Anthropic Blog",    "url": "https://www.anthropic.com/rss.xml"},
    {"name": "TechCrunch AI",     "url": "https://techcrunch.com/category/artificial-intelligence/feed/"},
    {"name": "The Verge AI",      "url": "https://www.theverge.com/rss/ai-artificial-intelligence/index.xml"},
    {"name": "VentureBeat AI",    "url": "https://venturebeat.com/category/ai/feed/"},
    {"name": "MIT Tech Review",   "url": "https://www.technologyreview.com/feed/"},
    {"name": "Wired AI",          "url": "https://www.wired.com/feed/category/artificial-intelligence/latest/rss"},
    {"name": "Ars Technica AI",   "url": "https://arstechnica.com/tag/artificial-intelligence/feed/"},
    {"name": "NVIDIA Blog",       "url": "https://blogs.nvidia.com/feed/"},
    {"name": "Microsoft AI",      "url": "https://blogs.microsoft.com/ai/feed/"},
    {"name": "HuggingFace Blog",  "url": "https://huggingface.co/blog/feed.xml"},
    {"name": "Import AI",         "url": "https://importai.substack.com/feed"},
    {"name": "The Rundown AI",    "url": "https://www.therundown.ai/feed"},
    {"name": "AI Business",       "url": "https://aibusiness.com/rss.xml"},
]

# ── Virality Keywords ─────────────────────────────────────────────────────────
HIGH_VIRALITY_KEYWORDS = [
    "launch", "release", "new", "breakthrough", "world first", "beats",
    "outperforms", "open source", "free", "gpt-5", "gemini", "claude",
    "llama", "deepseek", "mistral", "agent", "multimodal", "vision",
    "video generation", "image generation", "voice", "coding", "reasoning",
    "million", "billion", "funding", "startup", "acquired", "ipo",
    "banned", "regulation", "leaked", "exclusive", "major update",
    "announced", "unveiled", "now available", "powered by ai",
    "faster", "cheaper", "free tier", "api", "tool", "automation"
]

AI_TOPIC_KEYWORDS = [
    "artificial intelligence", "machine learning", "deep learning", "llm",
    "large language model", "chatgpt", "openai", "google ai", "gemini",
    "claude", "anthropic", "deepseek", "meta ai", "mistral", "grok",
    "neural network", "transformer", "diffusion", "stable diffusion",
    "midjourney", "dall-e", "sora", "runway", "elevenlabs", "ai model",
    "generative ai", "gen ai", "ai agent", "rag", "fine-tuning",
    "computer vision", "nlp", "text to image", "text to video",
    "ai tool", "ai startup", "ai funding", "ai regulation", "ai safety"
]


def _score_article(article: Dict) -> float:
    """Score an article for virality and relevance (0-100)"""
    score = 0.0
    text = (article.get("title", "") + " " + article.get("summary", "")).lower()

    # Recency score (max 40 pts)
    pub_date = article.get("published_parsed")
    if pub_date:
        try:
            pub_dt = datetime(*pub_date[:6])
            hours_old = (datetime.utcnow() - pub_dt).total_seconds() / 3600
            if hours_old < 6:
                score += 40
            elif hours_old < 12:
                score += 32
            elif hours_old < 24:
                score += 20
            elif hours_old < 48:
                score += 8
        except Exception:
            score += 5

    # AI keyword match (max 30 pts)
    ai_matches = sum(1 for kw in AI_TOPIC_KEYWORDS if kw in text)
    score += min(ai_matches * 3, 30)

    # Virality keyword match (max 30 pts)
    viral_matches = sum(1 for kw in HIGH_VIRALITY_KEYWORDS if kw in text)
    score += min(viral_matches * 2.5, 30)

    return round(score, 2)


def _fetch_rss_feeds() -> List[Dict]:
    """Fetch and parse all RSS feeds"""
    articles = []
    for feed_info in RSS_FEEDS:
        try:
            feed = feedparser.parse(feed_info["url"])
            for entry in feed.entries[:5]:  # Top 5 per feed
                articles.append({
                    "title": entry.get("title", ""),
                    "summary": entry.get("summary", entry.get("description", ""))[:500],
                    "url": entry.get("link", ""),
                    "source": feed_info["name"],
                    "published_parsed": entry.get("published_parsed"),
                    "published_str": entry.get("published", ""),
                })
        except Exception as e:
            print(f"[RSS] Failed {feed_info['name']}: {e}")
        time.sleep(0.3)
    return articles


def _fetch_newsapi(query: str = "artificial intelligence OR ChatGPT OR Gemini OR Claude AI") -> List[Dict]:
    """Fetch from NewsAPI.org if key is available"""
    if not settings.NEWS_API_KEY:
        return []
    try:
        yesterday = (datetime.utcnow() - timedelta(days=1)).strftime("%Y-%m-%d")
        resp = requests.get(
            "https://newsapi.org/v2/everything",
            params={
                "q": query,
                "from": yesterday,
                "sortBy": "publishedAt",
                "language": "en",
                "pageSize": 30,
                "apiKey": settings.NEWS_API_KEY,
            },
            timeout=10
        )
        data = resp.json()
        articles = []
        for a in data.get("articles", []):
            articles.append({
                "title": a.get("title", ""),
                "summary": a.get("description", "")[:500],
                "url": a.get("url", ""),
                "source": a.get("source", {}).get("name", "NewsAPI"),
                "published_parsed": None,
                "published_str": a.get("publishedAt", ""),
            })
        return articles
    except Exception as e:
        print(f"[NewsAPI] Error: {e}")
        return []


def _fetch_reddit_ai() -> List[Dict]:
    """Fetch trending posts from AI subreddits via RSS (more reliable than JSON API)"""
    subreddits = ["artificial", "MachineLearning", "ChatGPT", "singularity", "AItools"]
    articles = []
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Accept": "application/json",
    }
    for sub in subreddits:
        try:
            # Use RSS feed instead of JSON API (more stable, less bot detection)
            feed = feedparser.parse(f"https://www.reddit.com/r/{sub}/hot.rss")
            for entry in feed.entries[:3]:
                title = entry.get("title", "")
                if len(title) > 10:
                    articles.append({
                        "title": title,
                        "summary": entry.get("summary", title)[:300],
                        "url": entry.get("link", ""),
                        "source": f"r/{sub}",
                        "published_parsed": entry.get("published_parsed"),
                        "published_str": entry.get("published", ""),
                    })
        except Exception as e:
            print(f"[Reddit] r/{sub} RSS error: {e}")
        time.sleep(0.5)
    return articles



def _clean_html(text: str) -> str:
    """Strip HTML tags from summary"""
    clean = re.compile('<.*?>')
    return re.sub(clean, '', text).strip()


def research_top_news(log_fn=None) -> List[Dict]:
    """
    Main research function.
    Returns top 5 scored AI news articles with full metadata.
    """
    def log(msg):
        print(f"[NewsAgent] {msg}")
        if log_fn:
            log_fn(msg)

    log("Starting AI news research...")

    # Gather from all sources
    all_articles = []

    log("Fetching RSS feeds...")
    rss = _fetch_rss_feeds()
    all_articles.extend(rss)
    log(f"  → {len(rss)} articles from RSS feeds")

    log("Fetching NewsAPI...")
    newsapi = _fetch_newsapi()
    all_articles.extend(newsapi)
    log(f"  → {len(newsapi)} articles from NewsAPI")

    log("Fetching Reddit AI communities...")
    reddit = _fetch_reddit_ai()
    all_articles.extend(reddit)
    log(f"  → {len(reddit)} posts from Reddit")

    log(f"Total raw articles: {len(all_articles)}")

    # Clean summaries
    for a in all_articles:
        a["summary"] = _clean_html(a["summary"])
        a["title"] = _clean_html(a["title"])

    # Remove duplicates (by title similarity)
    seen_titles = set()
    unique_articles = []
    for a in all_articles:
        key = re.sub(r'\W+', '', a["title"].lower())[:50]
        if key not in seen_titles and len(a["title"]) > 10:
            seen_titles.add(key)
            unique_articles.append(a)

    log(f"Unique articles after dedup: {len(unique_articles)}")

    # Score all articles
    for a in unique_articles:
        a["score"] = _score_article(a)

    # Sort by score
    scored = sorted(unique_articles, key=lambda x: x["score"], reverse=True)

    # Take top 5
    top5 = scored[:5]

    log(f"Top 5 selected:")
    for i, a in enumerate(top5, 1):
        log(f"  #{i} [{a['score']}] {a['title'][:80]}")

    return top5
