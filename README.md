# 🤖 AI Instagram News Automation System

A fully autonomous AI-powered Instagram automation system that researches the latest AI news daily, generates premium carousel posts, and publishes them automatically at 9:00 AM.

---

## ✨ Features

- **📡 AI News Research** — Monitors 15+ RSS feeds, NewsAPI, Reddit AI communities
- **🤖 AI Content Generation** — Google Gemini generates slide copy, captions & hashtags
- **🎨 Premium Carousel Design** — Pillow renders 5 dark futuristic 1080×1080 slides per post
- **📤 Instagram Auto-Publish** — Posts via instagrapi (username/password, no API needed)
- **⏰ Daily Scheduler** — 8:00 AM research → 9:00 AM publish (fully automatic)
- **📊 Analytics Tracking** — Engagement metrics stored in SQLite
- **🖥 Live Dashboard** — Futuristic web UI with carousel previews, logs, analytics

---

## 🚀 Quick Start

### Step 1: Install & Run

```bash
# Double-click start.bat  OR  run in terminal:
start.bat
```

This will:
1. Install all Python dependencies
2. Create `.env` config file
3. Start the server at http://localhost:8000

### Step 2: Configure

Open http://localhost:8000 and go to **Settings** to enter:

| Setting | Where to get it |
|---------|----------------|
| Instagram Username | Your IG account username |
| Instagram Password | Your IG account password |
| Gemini API Key | [aistudio.google.com](https://aistudio.google.com) (free) |
| NewsAPI Key | [newsapi.org](https://newsapi.org/register) (optional, free) |

### Step 3: Test

Click **"Run Now"** on the dashboard to immediately run the full pipeline (research → generate → publish).

---

## 📋 Daily Schedule

| Time (IST) | Action |
|------------|--------|
| 8:00 AM | AI research starts (15+ sources) |
| 8:15 AM | Content generation (Gemini AI) |
| 8:30 AM | Carousel slides rendered |
| 9:00 AM | All 5 posts published to Instagram |

> Schedule can be changed in the Settings page.

---

## 🔑 Requirements

- **Python 3.10+** — [Download](https://python.org)
- **Instagram account** — Business/Creator or personal account
- **Google Gemini API key** — Free at [aistudio.google.com](https://aistudio.google.com)
- Internet connection

---

## 📁 Project Structure

```
agent/
├── backend/
│   ├── main.py               # FastAPI server + scheduler
│   ├── news_agent.py          # News research (RSS, Reddit, NewsAPI)
│   ├── content_engine.py      # Gemini AI content generation
│   ├── carousel_generator.py  # Pillow image renderer
│   ├── instagram_publisher.py # instagrapi posting
│   ├── database.py            # SQLite database
│   ├── config.py              # Settings
│   └── requirements.txt
├── frontend/
│   ├── index.html             # Dashboard
│   ├── style.css              # Dark futuristic UI
│   └── app.js                 # Dashboard logic
├── output/
│   └── images/               # Generated carousel images
├── data/
│   └── automation.db         # SQLite database
├── .env                      # Your credentials (auto-created)
└── start.bat                 # Windows launcher
```

---

## ⚠️ Notes

- Instagram may occasionally require email/phone verification for new logins. Complete verification once manually, then the system saves the session.
- If you have 2FA enabled on Instagram, disable it or handle the verification prompt.
- The system posts 5 carousels in one 9:00 AM batch with 30-second gaps between posts.
- All generated images are saved in `output/images/` and visible in the dashboard.

---

## 🛠 Manual Controls

From the dashboard you can:
- **Run Research Now** — fetch latest AI news immediately
- **Publish Now** — publish today's queued posts immediately  
- **Run Full Pipeline** — research + generate + publish at once
- **Preview** — click any post card to see all 5 slides
- **Publish Individual** — publish a specific post from the Posts page
