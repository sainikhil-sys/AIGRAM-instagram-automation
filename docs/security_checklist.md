# Security Checklist

Verify these security audits to prevent data leakage, unauthorized pipeline modifications, or account compromises.

---

## 1. Secrets & Credentials Management
- [ ] **No Raw Secrets in Source Control**: Ensure the `.env` file containing database passwords and API keys is excluded from your Git commits. 
- [ ] **Dynamic Credential Masking**: Confirm that the `/api/config` GET endpoint masks sensitive credentials. It must return values like `***` for active passwords/keys, preventing browser inspect panels from exposing secrets.
- [ ] **Dynamic Configurations Storage**: Dynamic configurations (Gemini/NewsAPI keys) saved in the database `config_store` must be secured behind authentication. In production, restrict access to the backend admin APIs.

---

## 2. Infrastructure & Tunnels
- [ ] **Database Connection SSL**: For Neon PostgreSQL connection URLs, ensure the parameter `?sslmode=require` is appended to enforce TLS transport encryption between the FastAPI app and your cloud database.
- [ ] **Upstash TLS Transport**: Verify your Redis connection string uses the secure prefix `rediss://` (with double 's'), guaranteeing encrypted network packets to Upstash.
- [ ] **CORS Restrictions**: In a production environment, modify CORS settings in `main.py` to change `allow_origins=["*"]` to explicitly list only your deployed Vercel frontend domain:
  ```python
  app.add_middleware(
      CORSMiddleware,
      allow_origins=["https://your-app-dashboard.vercel.app"],
      allow_credentials=True,
      allow_methods=["*"],
      allow_headers=["*"],
  )
  ```

---

## 3. Instagram publishing Security
- [ ] **Rate Limiting Delays**: Ensure the publishing spacing interval between carousels is kept at or above 30 seconds.
- [ ] **Session Persistence**: Keep Instagram session tokens cached under `data/sessions/instagram_session.json` to prevent repeated password logins. Logins from new cloud IP addresses too frequently trigger security challenges.
- [ ] **Disable 2FA temporarily or handle challenges**: If Two-Factor Authentication is active, ensure you are ready to input the SMS/Authenticator verification codes in the console or temporarily disable 2FA for the automated publisher account to run autonomously.

---

## 4. Telemetry & Telemetry Exposed Pages
- [ ] **Restrict Telemetry Endpoint**: The `/metrics` endpoint exposes runtime diagnostic statistics. Ensure your API gateway or reverse proxy restricts access to `/metrics` so that only internal Prometheus scraper agents can query it.
- [ ] **Sentry Exception Filters**: Ensure Sentry configuration filters out raw SQL database password strings from logs by sanitizing headers and payloads in `sentry_sdk.init()`.
- [ ] **Inputs validation**: All endpoints parsing JSON configurations (such as `/api/config`) must validate inputs using strict Pydantic parsing models.
