# Enterprise Cloud Deployment Guide

This guide details instructions on how to deploy AIGRAMP and its supporting resources to production-grade distributed cloud infrastructures.

---

## 1. Database & Caching Provisioning

### Neon PostgreSQL (Relational Database)
1. Go to [Neon.tech](https://neon.tech/) and sign up.
2. Create a new project named `aigram-db` and select your target region.
3. Once created, copy the connection URI from your dashboard. It looks similar to:
   `postgresql://[user]:[password]@[hostname]/neondb?sslmode=require`
4. Save this URI for your backend configurations (`DATABASE_URL`).

### Upstash Redis (Cache & Lock Coordinator)
1. Sign up at [Upstash.com](https://upstash.com/).
2. Click **Create Database**. Name it `aigram-cache` and choose **Redis**.
3. Enable TLS encryption.
4. Copy the connection string under the **Rediss URL** section. It should start with `rediss://`.
5. Save this URI for your backend configurations (`REDIS_URL`).

### Cloudinary (Asset Storage CDN)
1. Create an account at [Cloudinary.com](https://cloudinary.com/).
2. On your Cloudinary Dashboard, copy your **Cloud Name**, **API Key**, and **API Secret**.
3. You can also construct your `CLOUDINARY_URL` using this pattern:
   `cloudinary://[api_key]:[api_secret]@[cloud_name]`
4. Save these credentials for your backend configurations.

---

## 2. Backend API Deployment (Railway)

We recommend **Railway.app** for backend deployment because it natively supports Dockerfile builds and integrates Postgres/Redis easily.

1. Connect your GitHub repository to Railway.
2. Click **New Project** → **Deploy from GitHub repo** and select your repository.
3. In the Railway UI, navigate to settings and define the variables below.

### Environment Variables for Backend:
| Variable | Description | Example |
| :--- | :--- | :--- |
| `DATABASE_URL` | Neon PostgreSQL Connection URI | `postgresql://alex:pwd@ep-blue-sky.us-east.neon.tech/neondb` |
| `REDIS_URL` | Upstash Redis connection URI | `rediss://default:pwd@us1-fast-wasp-314.upstash.io:6379` |
| `CLOUDINARY_URL` | Cloudinary Connection String | `cloudinary://123:abc@my-cloud-name` |
| `GEMINI_API_KEY` | Google Gemini 2.0 API Key | `AIzaSyD...` |
| `NEWS_API_KEY` | NewsAPI key (Optional) | `9b3f...` |
| `SENTRY_DSN` | Sentry Python DSN (Optional) | `https://sentry.io/1234` |
| `HOST` | Bind Host Address | `0.0.0.0` |
| `PORT` | Bind Server Port | `8000` |

4. Railway automatically detects `/backend/Dockerfile` if your source root is pointed to `/backend` (or if you configure root build context).
5. Deploy. Railway will allocate a public domain, e.g., `https://aigram-production.up.railway.app`. Use this URL for your frontend setup.

---

## 3. Frontend Deployment (Vercel)

Vercel is ideal for serving Vite/React Single Page Applications.

1. Sign up on [Vercel.com](https://vercel.com/) and click **Add New Project**.
2. Select your GitHub repository.
3. Configure the following build options:
   - **Framework Preset**: Vite
   - **Root Directory**: `frontend`
   - **Build Command**: `npm run build`
   - **Output Directory**: `dist`
4. Add the following **Environment Variables**:

| Variable | Description | Example |
| :--- | :--- | :--- |
| `VITE_API_URL` | Public URL of your deployed Railway Backend | `https://aigram-production.up.railway.app` |
| `VITE_SENTRY_DSN` | Sentry React project DSN (Optional) | `https://sentry.io/5678` |

5. Click **Deploy**. Vercel will build the React SPA and serve it on a secure edge network.

---

## 4. Monitoring & Telemetry Dashboard Setup

### Sentry Error Tracking
1. Create a project in [Sentry.io](https://sentry.io/) for Python (backend) and React (frontend).
2. Configure the DSN keys in your environment variables. Unhandled server exceptions or frontend errors will automatically stream into Sentry.

### Prometheus & Grafana Telemetry
1. Expose your backend server `/metrics` endpoint to a Prometheus collector.
2. In a cloud setup, deploy a standalone Prometheus collector pointing its scraper target configuration file to the backend IP/host.
3. Launch Grafana and configure Prometheus as a data source.
4. Import the standard FastAPI dashboard configurations to display latency spikes, request logs, and cron scheduler task details.
