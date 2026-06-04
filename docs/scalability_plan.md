# Scalability & Growth Plan

This document outlines strategies for scaling the system to support higher volumes of posts, multiple accounts, high-availability deployments, and larger workloads.

---

## 1. High Availability & Backend API Scaling

### Multiple API Instance Replicas
You can scale the FastAPI backend container (`aigram_backend`) horizontally to run multiple instances (e.g. across multiple nodes in AWS ECS or Railway):
- **Stateless Design**: The FastAPI server is completely stateless. Session details are saved in Upstash Redis, and post metadata is saved in Neon PostgreSQL.
- **Load Balancing**: Place a standard load balancer (e.g. AWS ALB or Railway's built-in router) in front of the instances. Incoming client dashboard calls will automatically load-balance across nodes.

### Double-Trigger Mitigation (Redis Locks)
To prevent duplicate job runs when running multiple API nodes, the scheduler uses **Redis distributed locking**:
1. When a node's APScheduler triggers a job (e.g., the 8:00 AM news research pipeline), it requests a lock key `lock:research_pipeline` with a 30-minute expiration.
2. Only one node will succeed in setting the key and running the task. Other nodes will fail to acquire the lock and will immediately skip execution.

---

## 2. Infrastructure Auto-Scaling

### Neon PostgreSQL Scaling
- Neon PostgreSQL uses serverless architecture. It automatically scales compute resources (CPU/RAM) up during intensive pipeline runs (like the 8:00 AM database writes) and scales down to zero during idle hours to save costs.
- Ensure the connection pool limits are configured dynamically based on the number of backend instances.

### Upstash Redis Cache Scaling
- Upstash Redis is serverless and bills per request. It handles spikes in traffic gracefully without manual configuration.
- We utilize Redis for:
  1. Live log lists: Minimizes heavy disk writes.
  2. News caching: Prevents repeated RSS and NewsAPI fetches on client page refreshes.

### Cloudinary CDN Deliveries
- Generated slide images are uploaded immediately to Cloudinary.
- Cloudinary optimizes and serves these images via its global CDN network (Akamai/Fastly). The React frontend requests these cached CDN links, keeping the load off our FastAPI backend.

---

## 3. Worker Node Migration (Celery/RQ)

For scaling beyond 5 posts per day or running multiple media accounts:
1. **Migrate from APScheduler to Celery/RQ**: Replace FastAPI background tasks with a distributed queue (using Redis as the message broker).
2. **Dedicated Worker Containers**: Split the codebase into two images:
   - `aigram_web`: Serves API routes and dashboard files.
   - `aigram_worker`: Runs the long-running research, Pillow rendering, and Instagram upload tasks.
3. This ensures client API calls remain highly responsive (low latency) even when the heavy Pillow image generation task is running.
