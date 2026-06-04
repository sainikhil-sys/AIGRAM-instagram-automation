# Production Checklist

Perform the following validation audits before switching the system to fully automated daily media operations:

---

## 1. Database & Cache Verification
- [ ] **Database Connection Pool**: Ensure `DATABASE_URL` references your Neon production database. Confirm the database engine has pooling parameters configured (`pool_size=10`, `max_overflow=20`) to prevent transaction exhaustion under concurrent load.
- [ ] **Locking State Verification**: Test that Upstash Redis connects successfully. Check database logs to ensure cron triggers successfully acquire and release distributed locks (`lock:research_pipeline` and `lock:publish_pipeline`).
- [ ] **Audit Trail Storage**: Check that database queries return logs under the `audit_logs` table after startup.

---

## 2. API Credentials & Security Checks
- [ ] **No Secrets Leak**: Verify that no passwords or API keys are written in source code files. Ensure `.env` is listed under `.gitignore`.
- [ ] **Gemini API Limits**: Check that your Google Gemini API key has appropriate billing and rate quotas enabled.
- [ ] **NewsAPI Quotas**: If using NewsAPI.org, ensure your account limits (e.g. 100 queries per day on developer accounts) can support the 8:00 AM daily job.
- [ ] **Cloudinary CDN Assets**: Test uploading a sample image. Verify it returns a public HTTPS CDN link.

---

## 3. Instagram Authentication Diagnostics
- [ ] **Diagnostics Test**: Log into the configuration dashboard and click **Test Instagram Connection**. Verify it returns a success message showing your user profile info, post counts, and follower count.
- [ ] **Challenge Resolution**: If the login fails with `ChallengeRequired` or `TwoFactorRequired`, inspect the backend terminal outputs. Log in manually on a mobile phone from the same region/proxy to confirm and trust the server's device connection attempt.
- [ ] **Interval Throttling**: Verify that the delay spacing between carousel publication queue runs is set to at least 30 seconds to respect Instagram's strict bot-activity detectors.

---

## 4. Telemetry & Error Logging
- [ ] **Sentry Telemetry**: Verify Sentry SDK links compile successfully at boot. Open the Sentry console and verify test errors trigger warnings.
- [ ] **Prometheus Harvest Check**: Visit the `/metrics` endpoint. Confirm it outputs Prometheus-compatible metrics data.
- [ ] **Health Status Verification**: Query the `/healthz` API endpoint. Confirm it returns a `200 OK` status with `{"status":"healthy", "postgres":"healthy", "redis":"healthy"}`.
