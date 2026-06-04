# 🤖 Enterprise AI Instagram News Automation System

A production-ready, cloud-first distributed system that automatically researches trending AI updates, generates high-fidelity Instagram carousel posts using Gemini AI, hosts assets on Cloudinary CDN, and schedules posting batches using distributed Redis locking and Neon PostgreSQL.

---

## 🏗 System Architecture

The project is re-engineered as a decoupled, secure, and production-ready microservices layout:

- **Frontend (Vercel)**: React SPA served with Vite, utilizing modern Outfit/Inter fonts, glowing glassmorphic components, and an interactive phone-simulator slideshow.
- **Backend API (Railway/AWS)**: FastAPI application running APScheduler. Configured for horizontal scaling using Upstash Redis locking to mitigate duplicate posting.
- **Database (Neon PostgreSQL)**: Relational tables storing post rankings, analytics, APScheduler runs, and a security **System Audit Log**.
- **Distributed Cache (Upstash Redis)**: Handles log streaming, news caching, and distributed locking.
- **Asset Storage (Cloudinary CDN)**: Serves generated slide graphics on a secure global CDN.
- **Monitoring & Diagnostics**: Fully instrumented with **Sentry** (exception captures) and **Prometheus** (metrics telemetry under `/metrics` visible via Grafana).

---

## ✨ Features

- **📡 AI News Research** — Monitors 15+ RSS feeds, NewsAPI, and Reddit, caching results in Redis.
- **🤖 AI Content Strategist** — Google Gemini 2.0 Flash constructs hook headlines, slide copy, captions, and hashtags.
- **🎨 Premium Carousel Design** — Pillow compiles 5 dark futuristic 1080×1080 slides per post.
- **☁️ Cloud Asset Storage** — Slides are automatically uploaded to Cloudinary for React rendering.
- **📤 Instagram Auto-Publish** — Publishes carousels batch-wise via instagrapi.
- **🔐 Distributed Locks** — Redis SETNX guards prevents scheduler duplication across scaled nodes.
- **📜 System Audit Logs** — Audit table monitors configuration overrides and pipeline triggers.
- **🖥 Interactive Dashboard** — React interface with swipes, configuration forms, diagnostic panels, and terminal logs.

---

## 🛠 Local Docker Quick Start

Launch the complete database, cache, backend, frontend, and telemetry monitors locally with a single command:

```bash
# 1. Copy environment template
copy .env.example .env

# 2. Spin up containers
docker-compose up -d --build
```

### Port Mappings:
- **React Frontend**: http://localhost:3000 (Served via Nginx)
- **FastAPI Backend**: http://localhost:8000 (Swagger docs at `/docs`, health checks at `/healthz`)
- **Prometheus Collector**: http://localhost:9090
- **Grafana Visualization**: http://localhost:3001 (Default credentials: `admin` / `admin`)

---

## 🚀 Cloud Deployment

### 1. Provision Services
- Set up a serverless PostgreSQL cluster at [Neon.tech](https://neon.tech/) and grab the connection URL.
- Create a serverless Redis database at [Upstash.com](https://upstash.com/) and copy the TLS connection URL (`rediss://`).
- Obtain Cloudinary credentials from [Cloudinary.com](https://cloudinary.com/).
- (Optional) Provision a project at [Sentry.io](https://sentry.io/) to get DSN keys.

### 2. Deploy Backend (Railway / AWS)
Set up a Railway project bound to the repository. The build context is automatically directed to `/backend/Dockerfile`. Populate the following environment variables:
- `DATABASE_URL` (Neon PostgreSQL)
- `REDIS_URL` (Upstash Redis)
- `CLOUDINARY_URL` / API credentials
- `GEMINI_API_KEY` (Google AI Studio)
- `NEWS_API_KEY` (NewsAPI.org, optional)
- `SENTRY_DSN` (Optional)

### 3. Deploy Frontend (Vercel)
Connect the repository to Vercel. Select `frontend` as the root directory, set framework preset to `Vite`, and add the following variable:
- `VITE_API_URL` (Deploved Railway backend URL)
- `VITE_SENTRY_DSN` (Optional)

---

## 📂 Project Structure

```
agent/
├── .github/workflows/deploy.yml   # GitHub Actions CI/CD Pipeline
├── backend/
│   ├── Dockerfile                 # Multi-stage Python compiler
│   ├── config.py                  # Environment loader & DB overrides
│   ├── database.py                # Neon PostgreSQL schemas & SQLAlchemy session
│   ├── redis_service.py           # Upstash Redis distributed locks & log stream
│   ├── cloudinary_service.py      # Cloudinary uploader integration
│   ├── main.py                    # FastAPI server entry point, metrics, & healthz
│   ├── news_agent.py              # RSS/Reddit aggregator
│   ├── content_engine.py          # Gemini AI content generation
│   ├── carousel_generator.py      # Pillow rendering engine
│   └── instagram_publisher.py     # instagrapi automation publisher
├── frontend/
│   ├── Dockerfile                 # React build and Nginx static host
│   ├── nginx.conf                 # SPA fallback configuration
│   └── src/                       # React components (Dashboard, Preview, Config, Logs)
├── docs/                          # Architectural and security guides
├── monitoring/                    # Prometheus scrapers configuration
└── docker-compose.yml             # Local multi-container orchestra
```

---

## 🔒 Security & Telemetry Compliance
- **No Stored Secrets**: Environment variables are resolved dynamically. dynamic configuration overrides are stored in the relational database `config_store`.
- **Encryption in Transit**: Connections to Neon and Upstash require SSL parameters.
- **Audit trails**: Every manual trigger, connection test, or configuration save generates an event entry under the `audit_logs` table.
