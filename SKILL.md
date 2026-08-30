---
name: backend-setup-skill
description: Use when setting up a secure backend using Python/FastAPI with JWT authentication, PostgreSQL, Docker, and Nginx for serving React/Tailwind frontends. Includes Redis for caching and enforces standardized backend architecture, security best practices, API design patterns, database migration strategies, containerization standards, and deployment readiness.
---

# Backend Setup Skill

## Overview

This skill establishes mandatory architectural standards, security protocols, API design patterns, database strategies, containerization standards, and deployment checklists for generating a production-ready Python/FastAPI backend with JWT authentication and Redis caching. Use this skill to ensure consistent backend design, prevent security vulnerabilities, enforce high performance, maintain fault tolerance, and verify deployment readiness across all backend development tasks.

---

## 1. Technology Stack & Architecture Standards

### 1.1. Core Backend Stack (Primary Choice)

Unless explicit requirements dictate otherwise, always default to the following stack for backend components:

| Layer                | Standard Technology   | Primary Use Case                                |
| :------------------- | :-------------------- | :---------------------------------------------- |
| **Backend Core**     | Python (FastAPI)      | Async RESTful APIs & Microservices              |
| **Relational DB**    | PostgreSQL            | Primary transactional relational database       |
| **ORM**              | SQLAlchemy (Async)    | Object-relational mapping (using asyncpg)       |
| **Migration Tool**   | Alembic               | Database schema versioning                      |
| **Authentication**   | JWT (JSON Web Tokens) | Stateless authentication mechanism              |
| **Password Hashing** | Argon2id              | Secure memory-hard password storage             |
| **Input Validation** | Pydantic V2           | Data validation (Mandate V2, forbid V1 syntax)  |
| **Caching**          | Redis                 | Session management, caching, rate limiting      |
| **Containerization** | Docker                | Container runtime                               |
| **Orchestration**    | Kubernetes (K8s)      | Production container orchestration & scaling    |
| **Reverse Proxy**    | Nginx / Cloud LB      | API Gateway, Load Balancing (Cloud handles SSL) |
| **CI/CD Pipeline**   | GitHub Actions/Jenkins| Automated testing, linting, building, & deploy  |
| **OS & Hosting**     | Ubuntu Server (Linux) | Target server operating system                  |

### 1.2. Backend Architecture Pattern

Choose the architectural pattern based on project complexity and scaling requirements:

- **Modular Monolith (Default Standard):**
  - Default for new backends, MVPs, and small-to-medium systems.
  - Enforce clear domain isolation (separate module folders, strict interfaces) while keeping deployment within a single unified service.
  - Maximizes development speed, simplifies database transactions, and minimizes infrastructure/DevOps complexity.
  - **Frontend Decoupling (Best Practice):** Modern SPAs (React/Tailwind) should be deployed independently to Edge CDNs (e.g., Vercel, Netlify, Cloudflare Pages) to optimize Time-to-First-Byte (TTFB). Avoid static bundling with the backend Nginx server in production unless strictly required by a legacy/isolated environment.

- **Microservices Architecture (Conditional Standard):**
  - Apply ONLY when specific modules require independent horizontal scaling, separate data isolation, or multi-team ownership.
  - Requires dedicated databases per service, an API Gateway (Nginx/Traefik), async inter-service messaging (Kafka/RabbitMQ/Redis Pub-Sub), or gRPC.

### 1.3. Software Design Patterns & SOLID Principles

Enforce clean, scalable code architecture across all backend components:

- **SOLID Principles:**
  - **S (Single Responsibility):** Classes, components, and modules must have one clear reason to change.
  - **O (Open/Closed):** Open for extension, closed for modification (e.g., using interfaces/abstract classes).
  - **L (Liskov Substitution):** Subtypes must be substitutable for their base types.
  - **I (Interface Segregation):** Keep interfaces small and client-focused rather than monolithic.
  - **D (Dependency Inversion):** Depend on abstractions (interfaces), not concrete implementations (e.g., Dependency Injection).
- **Core Design Patterns:**
  - **Repository & Service Layer Pattern (Strict DI):** Separate data access logic (`crud/`) from core business rules (`services/`). **Critical Rule:** The `services/` layer MUST define its own Interfaces (Abstract Base Classes). The `crud/` layer implements these interfaces. *Warning: Never instantiate the CRUD implementation directly inside the FastAPI Router. You MUST use `app.dependency_overrides[IUserRepository] = get_user_crud` at app bootstrap to wire the interface to the implementation, keeping the router fully decoupled.*
  - **DTO (Data Transfer Object) Pattern:** Enforce strict separation between external API schemas (Pydantic V2) and internal DB models.
  - **Factory & Strategy Patterns:** Use for configurable business rules, payment gateway integrations, or notification provider switching.
  - **Observer / Event-Driven Pattern:** Use pub-sub events for async background tasks (e.g., sending emails after user registration).

### 1.4. API Design & Versioning Standards

- **API Versioning:** Prefix all public API routes with explicit versioning (e.g., `/api/v1/...`).
- **DTO Structure Versioning:** Data Transfer Objects (DTOs) must also be versioned in folder structures (e.g., `v1/requests`, `v1/responses`) to ensure backward compatibility.
- **RESTful Conventions:** Use standard HTTP methods (`GET`, `POST`, `PUT`, `PATCH`, `DELETE`) and proper HTTP status codes (200, 201, 204, 400, 401, 403, 404, 422, 500).
- **Binary Data (I/O Bottleneck):** NEVER upload large files (PDFs, images) directly through the Backend API. This blocks worker I/O and risks data loss if the K8s pod is evicted. You MUST implement **Pre-signed URLs** (Direct Upload). The frontend requests a temporary signed URL from the backend, then uploads the file directly to AWS S3/MinIO. The backend only handles a webhook to save metadata.
- **Standardized Response Envelope:** Format API responses consistently:
  ```json
  {
    "success": true,
    "data": { ... },
    "error": null
  }
  ```
- **OpenAPI / Swagger Spec:** Maintain auto-generated OpenAPI documentation for development, but MUST disable it (`openapi_url=None`) in Production to prevent API reconnaissance and topology leaks.

### 1.5. Modern & Scalable Database Design

- **Primary Keys:** Mandate the use of UUIDs (specifically UUIDv7 for time-sorted locality) or ULIDs over auto-incrementing integers. This prevents ID enumeration vulnerabilities and supports distributed scaling and sharding. *(Note: Since PostgreSQL < 16 lacks native UUIDv7, generate these safely at the application layer using libraries like `uuid6` in Python to prevent collision during high-concurrency inserts).*
- **Audit Trails:** Enforce `created_at` and `updated_at` timestamps on all critical entities. For systems with user authentication, also include `created_by` and `updated_by` columns for compliance and tracking.
- **Soft Deletion Strategy:** Implement `deleted_at` timestamps to soft-delete records instead of hard `DELETE` queries. This maintains referential integrity, preserves historical data, and allows for accidental deletion recovery. Hard deletes should only be used for strict data privacy/GDPR compliance. *Critical (Soft Delete DB Trap):* You MUST NOT use standard `UNIQUE` constraints on tables with soft delete (e.g., `users.email`), or returning users will crash the API (IntegrityError). You MUST use a **Partial Unique Index** in PostgreSQL: `CREATE UNIQUE INDEX ON users (email) WHERE deleted_at IS NULL;`.
- **Flexible Data Modeling (JSONB):** Leverage PostgreSQL's `JSONB` columns for semi-structured data (e.g., dynamic metadata, user preferences) while keeping core relational attributes properly normalized.
- **Scaling & Partitioning Readiness:** Design large tables (like audit logs or time-series metrics) with PostgreSQL Table Partitioning in mind (e.g., partitioning by month or year) to prevent infinite monolithic table growth.

---

## 2. Security & Defense-in-Depth Protocols

All backend code, API endpoints, and configuration files MUST strictly comply with these security layers:

### 2.1. Authentication & Authorization

- **JWT Authentication:** Pass tokens via Authorization header as Bearer tokens (for API) or HttpOnly, Secure, and SameSite cookies (for web applications). *Critical: Access Tokens must have an ultra-short lifespan (e.g., 5-15 mins). To maintain stateless performance while retaining the ability to force-logout users, use a Hybrid approach: only query the Redis blacklist on highly sensitive endpoints (e.g., password change, payments).*
  - *Warning (The Third-Party Cookie Apocalypse):* Modern browsers (Safari, Chrome) actively block third-party cookies by default. You MUST NOT rely on `SameSite=None` across different domains (e.g., `app.vercel.app` vs `api.company.com`). You MUST configure DNS so both frontend and backend share a Registrable Domain (e.g., `app.company.com` and `api.company.com`). This makes the cookie First-Party, allowing you to safely use `SameSite=Lax`, which inherently protects against CSRF and bypassing browser blocks.
- **Access Control:** Enforce Role-Based Access Control (RBAC) / Attribute-Based Access Control (ABAC) on all protected routes.
- **Identity Providers:** Integrate OAuth2 / OpenID Connect for third-party identity providers where applicable.
- **Session Control:** Enforce strict Token Expiration and Refresh Token rotation. *Critical: Do NOT use Redis distributed locks for Refresh Token rotation, as it creates bottlenecks and blocks concurrent frontend requests. Implement a **Grace Period** instead. However, Grace Periods alone are vulnerable to Token Replay attacks. You MUST implement a **Token Family Lifecycle** (Idempotency): when Token A is refreshed to Token B, store `A -> B` in Redis for 30s. If a late request brings Token A, return Token B. If Token A is used again to create a NEW branch, immediately revoke the entire Token Family (A and B) as it indicates token theft.* *Warning (Mass-Logout DDoS):* If the Redis pod crashes and memory is lost, the entire Token Family is wiped, forcing thousands of users to re-login simultaneously and DDoSing your Argon2id hashing API. Auth state in Redis MUST use **High Availability (Sentinel/Cluster)** and configure `appendfsync always` to prevent data loss.

### 2.2. Injection Prevention & Input Handling

- **SQL Injection:** Exclusively use ORMs (SQLAlchemy) with parameterized queries. Never concatenate raw SQL strings.
- **Cross-Site Scripting (XSS):** Sanitize all dynamic inputs and rely on framework-level auto-escaping where applicable.
- **Code Execution:** Absolutely forbid execution of arbitrary strings (`eval()`, `exec()`, or unsafe OS shell commands).
- **Prompt Injection (AI Integration):** Implement strict input validation, data sanitization, context bounding, and output escaping for any LLM interaction.

### 2.3. Cryptography & Web Protection

- **Data Exchange:** Implement RSA Public Key Infrastructure (PKI) key pairs or AES-256 for sensitive payload encryption where needed.
- **Web Defense:** Enforce strict CORS origin whitelisting and strict Rate Limiting on all public API endpoints. *Critical (CORS Masking Trap):* If your architecture uses a Reverse Proxy (Nginx/Ingress) in front of FastAPI, you MUST disable `CORSMiddleware` in FastAPI in production. Shift the responsibility of handling Preflight `OPTIONS` and injecting CORS headers entirely to the Gateway layer. Otherwise, any request blocked by Nginx (e.g. 413) or crashing before the FastAPI router (e.g. 500) will lack CORS headers, masking the true error as a fake "CORS Error" in the frontend. *Critical (The Proxy IP Trap):* When running behind a Load Balancer, the `X-Forwarded-For` header must be handled carefully. If you rate-limit by IP without parsing it, the LB IP will be banned, locking everyone out. If you parse it blindly, attackers can spoof it. You MUST run Uvicorn with `--proxy-headers` AND `--forwarded-allow-ips="<LB_IP>"` to safely resolve the true client IP.
- **Transport Security:** Enforce SSL/TLS encryption (HTTPS / WSS). In local/VPS environments, use Nginx for SSL termination. In Cloud/K8s environments, offload SSL termination to the Cloud Load Balancer (ALB) or Ingress Controller to simplify certificate management.
- **Server Defense:** Configure UFW firewall (allow 80/443/SSH only), Fail2Ban, and ed25519 SSH key authentication.

### 2.4. Database Integrity & Transaction Management (ACID)

- **ACID Guarantees:** Multi-step database operations MUST be wrapped in explicit database transactions (`BEGIN`, `COMMIT`, `ROLLBACK`) to guarantee Atomicity, Consistency, Isolation, and Durability. *Critical (TOCTOU Trap):* Standard transactions do NOT prevent Time-of-Check to Time-of-Use (TOCTOU) race conditions (e.g., double-spending). You MUST NEVER use a naive "Read-then-Update" pattern for money, inventory, or shared states. You MUST enforce **Pessimistic Locking** (`SELECT ... FOR UPDATE`) to lock the row, or **Optimistic Locking** (using a `version_id` column).
- **Transaction Scope:** Keep transactions as short and tight as possible. NEVER invoke slow I/O operations (e.g., third-party HTTP requests, email sending) inside an open DB transaction.
- **Isolation & Concurrency:** Configure proper transaction isolation levels (e.g., `READ COMMITTED` or `REPEATABLE READ`) and handle deadlocks/race conditions using optimistic/pessimistic locking where needed.
- **Data Integrity Constraints:** Enforce schema-level constraints (Foreign Keys, Unique Indexes, NOT NULL, Check Constraints) directly in PostgreSQL schemas.

### 2.5. Database Schema Migrations

- **Version-Controlled Migrations:** Never alter production database schemas manually. Use automated migration tools (Alembic).
- **Backward Compatibility:** Write database migrations that allow zero-downtime deployment (e.g., expand-and-contract pattern for schema changes).
- **The Alembic/Asyncpg Trap:** Alembic defaults to synchronous execution. If your app uses `asyncpg`, running `alembic upgrade head` will crash with "Cannot use a synchronous engine with an async driver". You MUST either modify `alembic/env.py` to run within `asyncio.run()`, or maintain a separate `SYNC_DATABASE_URL` (using `psycopg2`) specifically for migrations.

### 2.6. Redis Security Specifics

- **Network Binding:** Bind Redis to localhost or internal network interfaces only (never expose to 0.0.0.0 in production).
- **Authentication:** Require a strong password for Redis access (use `requirepass` in redis.conf).
- **Command Protection:** Disable or rename dangerous commands (FLUSHALL, FLUSHDB, KEYS, etc.) in production environments.
- **Data Encryption:** Consider using Redis ACLs and encryption for sensitive data at rest.
- **Monitoring:** Monitor Redis for unusual connection patterns or command usage.
- **Persistence:** Configure RDB/AOF persistence appropriately based on use case (cache vs. session store).

---

## 3. Performance, Resilience & Observability Guidelines

Maintain high throughput, fast response times, fault tolerance, and clear system visibility across all backend layers:

### 3.1. Database Query Performance & Connection Pooling

- **Async Database Drivers:** Explicitly mandate the use of `asyncpg` (Async SQLAlchemy drivers) to prevent blocking FastAPI's asynchronous event loop. Using synchronous drivers (e.g., `psycopg2`) in async routes will severely degrade performance.
- **Query Optimization:** Prevent N+1 query problems by using eager loading (`joinedload` / `selectinload`).
- **Index Management:** Add composite and partial indexes on frequently filtered, joined, or sorted columns. Avoid unindexed table scans.
- **Connection Pooling:** Always configure DB connection pools (SQLAlchemy Pool) with max pool sizes and timeout limits. *Critical (Pool Poisoning):* You MUST configure your SQLAlchemy Engine with `pool_pre_ping=True`. If the database restarts or drops connections overnight, existing connections in the pool become dead (Broken Pipe). Without `pool_pre_ping=True`, the backend will repeatedly serve dead connections and return 500 Internal Server Errors until manually restarted. *Warning (The HPA Connection Paradox):* When using Kubernetes Auto-scaling (HPA), Application-level pooling is dangerous. If HPA scales to 20 Pods with a pool size of 20, you instantly hit PostgreSQL with 400 connections, crashing it (`FATAL: sorry, too many clients already`). You MUST place a Centralized Connection Pooler (e.g., PgBouncer, Pgpool-II, AWS RDS Proxy) in front of the database to regulate physical connections. *Critical (The Silent Connection Leak):* When standing behind PgBouncer in Transaction Mode, you MUST pass `poolclass=NullPool` to `create_async_engine` in FastAPI. This forces FastAPI to give up connection pooling and return all physical connections back to PgBouncer immediately, preventing pool-on-pool deadlocks and timeouts.
- **Database Pagination:** Enforce Keyset (Cursor) or Limit-Offset pagination on all list endpoints to avoid loading unbounded datasets into memory.

### 3.2. Caching Strategy (Redis)

- **Read-Aside Caching:** Cache high-read/low-write query results in Redis with appropriate Time-To-Live (TTL) expiration.
- **Cache Invalidation:** Implement explicit cache purging or event-driven invalidation when underlying records are updated.
- **Cache Stampede Protection:** Use lock mechanisms or probabilistic early expiration for expensive cached data.
- **Serialization:** Use efficient serialization (JSON, MessagePack, or Pickle) for cached objects.
- **Key Naming:** Use consistent, namespaced key patterns (e.g., `user:{id}:profile`, `api:v1:users:list`).
- **Memory Management:** Set appropriate maxmemory policies (e.g., `allkeys-lru`) and monitor memory usage.

### 3.3. System Resilience & Fault Tolerance

- **Container Dependency & Healthchecks:** In Docker Compose, backend service MUST use `depends_on` with `condition: service_healthy` coupled with explicit `healthcheck` definitions on database containers (PostgreSQL / Redis). This ensures backend nodes patiently wait for database engines to fully initialize before opening connections, preventing startup crash loops upon `docker compose up`.
- **Timeouts & Deadlines:** Configure explicit timeouts on all HTTP requests, database queries, and Redis operations.
- **Retries & Backoff:** Implement Retry with Exponential Backoff and Jitter for transient network or external API failures.
- **Graceful Shutdown:** Intercept `SIGTERM` / `SIGINT` signals to drain in-flight HTTP requests and gracefully close database connection pools before process exit. *Critical (The SIGTERM Race Condition):* In Kubernetes, when a Pod receives `SIGTERM`, `kube-proxy` networking (iptables) takes a few seconds to stop routing traffic to it. If the app shuts down instantly, users hit 502 Bad Gateway errors. You MUST add a Lifecycle Hook `preStop: exec: command: ["/bin/sleep", "5"]` in the Deployment YAML to intentionally delay the pod's shutdown until K8s networking is fully updated.

### 3.4. Structured Logging & Tracing

- **Structured JSON Logging:** Output all application logs in structured JSON format. *Critical (Compliance Trap):* Dumping full request JSON payloads into logs can expose plaintext passwords, JWTs, or medical data (PHI) to ELK/Datadog, violating GDPR/HIPAA. You MUST implement a **Log Redaction/Masking Middleware** to automatically replace sensitive keys with `***REDACTED***` before writing to standard out.
- **Request Trace ID:** Generate and propagate a unique `X-Request-ID` / `trace_id` header across all log entries and downstream API calls.

### 3.5. Concurrency, Scaling & Asynchronous Workers

- **Async I/O & Server Worker Tuning:** Utilize non-blocking async I/O for all network/DB tasks. *Warning (The Cgroup CPU Illusion):* Never let the application auto-detect workers via `multiprocessing.cpu_count()` in Docker/Kubernetes. This reads the host's physical cores, ignoring the container's CPU limits, leading to immediate OOMKilled or severe CPU Throttling. You MUST dynamically calculate `WEB_CONCURRENCY` based on the K8s CPU limits (e.g., `(CPU Limit * 4) + 1`). Do not hardcode arbitrary numbers like `2`.
- **Distributed Locking & Race Prevention:** Use distributed locks (e.g., Redis `Redlock`) to prevent race conditions and double-processing when updating shared state across concurrent backend instances.
- **Asynchronous Task Queues:** Offload heavy or long-running tasks (emailing, PDF generation, video encoding) to background worker queues (e.g., Celery, ARQ) to avoid blocking HTTP request handlers. *Warning (The Poison Pill Trap):* If a background task fails due to a deterministic logic error (e.g., bad email format crashing the parser), the worker will retry it infinitely, exhausting CPU and freezing the queue. You MUST configure a **Dead Letter Queue (DLQ)** and set `max_retries`. Failing tasks must be moved to the DLQ after ~3 attempts to free up the worker.

---

## 4. Mandatory Development Checklist

Before marking any backend feature, API, or infrastructure setup as complete, verify every item below:

### [ ] Backend & API Quality Checklist

1. **API Security:** All non-public endpoints require authentication, RBAC authorization, and active rate limiting.
2. **API Design & Versioning:** Routes are versioned (`/v1/`), DTO schemas are versioned in directory structures (`v1/requests`, `v1/responses`), adhere to REST standards, and return standardized JSON envelopes.
3. **Architecture & Patterns:** Logic follows Repository/Service pattern, separating data access from API schemas (DTOs).
4. **Request Validation:** Inbound request models validate schemas strictly (Pydantic).
5. **Data Access & Migrations:** DB queries are parameter-bound and optimized (N+1 queries resolved). Multi-step state mutations MUST use explicit ACID database transactions. Schemas are updated via migration scripts.
6. **Concurrency & Async Tasks:** Heavy operations are offloaded to background task queues. Shared state updates across instances use distributed locking.
7. **Exception Handling:** Global exception handlers catch unhandled errors without leaking stack traces or internal server details to clients.
8. **Scalable DB Design:** Schemas utilize UUID/ULID for primary keys, include audit timestamps (`created_at`, `updated_at`), and implement soft deletion (`deleted_at`). *Critical (Naive Datetime Bomb):* NEVER use `datetime.utcnow()` (deprecated in Python 3.12+). You MUST use Timezone-Aware datetimes (`datetime.now(timezone.utc)`) in Python and declare `TIMESTAMP WITH TIME ZONE` (`DateTime(timezone=True)`) in PostgreSQL to prevent audit logs from silently shifting across timezones.

### [ ] QA & Testing Checklist

1. **Unit Tests:** Critical business logic, helpers, and utility functions have passing unit tests (Pytest) with properly mocked dependencies (DB sessions, external APIs, Redis).
2. **Integration Tests:** Endpoint routes and DB operations are covered with mock-backed integration tests. Ensure complete flows (e.g., User Registration -> Login -> Access Protected Route) are tested.
3. **Edge Cases & Error Handling:** Error boundaries, invalid inputs, duplicate data entries, and unexpected network drops are explicitly tested.
4. **Authentication Tests:** Validate login, refresh token rotation, protected route access, role-based permissions, and expired token rejection.
5. **Cache Tests:** Validate Redis caching functionality, TTL expiration, cache invalidation on data updates, and fallback mechanisms if Redis is down.
6. **Load & Performance Testing:** Validate API endpoints under concurrency (using Locust or k6) to ensure they meet response time SLAs and to verify connection pooling limits.

### [ ] DevOps & Infrastructure Checklist

1. **Environment Variables:** All secrets and credentials are loaded via `.env` or Secret Managers (e.g., AWS Secrets Manager, K8s Secrets)—NEVER hardcoded in source.
2. **Network Isolation:** Databases (PostgreSQL / Redis) and internal services are isolated from public network access.
3. **Volume Persistence:** Persistent storage paths are mapped correctly (or configured in K8s PersistentVolumes) to prevent data loss across container restarts.
4. **Container Health & Dependencies:** Dockerfiles multi-stage builds are optimized. Health checks are defined for DB/Redis containers. Docker Compose enforces `depends_on: { condition: service_healthy }`. K8s uses standard `livenessProbe` and `readinessProbe`.
5. **Pipeline & Infrastructure Concurrency:** CI/CD deployment pipelines (GitHub Actions/Jenkins) enforce concurrency locks to prevent overlapping deployments. IaC uses state locking.
6. **Monitoring & Logging:** Centralized error logging (Sentry), structured JSON logs with trace IDs, and metrics collection (Prometheus/Grafana) are configured.
7. **Redis Security:**
   - Redis is bound to internal networks only
   - Strong password is configured for Redis access
   - Dangerous commands are disabled/restricted in production
   - Memory limits are set appropriately
   - Redis persistence is configured correctly for the use case
8. **Container Security:** Containers run as non-root users and file system permissions are restricted. Images are scanned for vulnerabilities (e.g., using Trivy) in the CI/CD pipeline.

---

## 5. Execution Rules & Red Flags

### Operational Rules

- **Never Assume Missing Context:** If an API payload or architecture detail is ambiguous, request clarification before writing speculative code.
- **Complete Code Files:** Output complete, runnable code or clear, precise insertion diffs. Never leave stub functions like `// handle this later`.
- **Test-Driven Rigor:** Provide automated tests alongside every new feature implementation.

### Red Flags - STOP and Fix

- 🚩 Hardcoding API keys, JWT secrets, or DB passwords in source control.
- 🚩 Executing multi-table or multi-step database mutations without explicit ACID transactions and rollback handling.
- 🚩 **Blocking the Event Loop:** Using synchronous SQLAlchemy drivers (`psycopg2`) or synchronous HTTP clients (`requests`) inside `async def` FastAPI routes.
- 🚩 **Stateful JWTs:** Querying Redis/DB on every single request to validate a JWT token's status.
- 🚩 **Unsafe Refresh Tokens:** Lacking a grace period or lock mechanism during refresh token rotation, causing double-refresh race conditions.
- 🚩 **Migration Collisions:** Allowing multiple K8s replicas to run `alembic upgrade head` simultaneously on startup.
- 🚩 Modifying production database schemas manually without version-controlled migration scripts.
- 🚩 Omitting `condition: service_healthy` in Docker Compose `depends_on` blocks for database dependencies, causing application startup crashes.
- 🚩 Running heavy or slow operations (e.g. PDF generation, sending emails) directly inside synchronous HTTP request threads.
- 🚩 Writing unindexed database queries or ignoring N+1 query performance bottlenecks.
- 🚩 Making outbound external HTTP calls without explicit timeouts or retry policies.
- 🚩 Catching generic exceptions (`except Exception: pass`) without logging or proper error handling.
- 🚩 Exposing raw database ports directly to `0.0.0.0` without firewall rules.
- 🚩 Disabling CORS, CSRF, or SSL verification as a shortcut during debugging.
- 🚩 Exposing Redis to public networks without authentication.
- 🚩 Using default Redis configuration without setting a strong password.
- 🚩 Leaving dangerous Redis commands (FLUSHALL, KEYS, etc.) enabled in production.
- 🚩 **OpenAPI Leak:** Leaving `/api/docs` enabled in production environments.
- 🚩 **InitContainer Downtime:** Running database schema migrations in a Kubernetes `InitContainer` during a Rolling Update. This causes old Pods to crash immediately when the schema changes. Migrations must be an isolated pre-deploy step.
- 🚩 **Third-Party Cookie Block:** Using `SameSite=None` HttpOnly cookies across different domains, which will be silently blocked by Safari/Chrome Privacy Sandbox. Use First-Party domains + `SameSite=Lax`.
- 🚩 **Alembic Sync Crash:** Running default synchronous Alembic migrations against an `asyncpg` database URL.
- 🚩 **Naive Datetime:** Using `datetime.utcnow()` and `TIMESTAMP WITHOUT TIME ZONE`, leading to catastrophic timezone shifts in production audit logs.
- 🚩 **Fake Dependency Injection:** Defining interfaces for services but hardcoding the concrete `crud/` instantiation directly inside the FastAPI Router instead of using `dependency_overrides`.
- 🚩 **Cgroup CPU Illusion:** Letting ASGI workers auto-scale based on `cpu_count()` inside containers, causing the app to spawn 64 workers on a 64-core node despite having a 0.5 CPU limit, leading to OOMKilled.
- 🚩 **Pool Poisoning:** Forgetting to enable `pool_pre_ping=True` in SQLAlchemy, causing 500 errors when the database restarts and connections become stale.
- 🚩 **Pydantic Secrets Blindness:** Mounting Docker Secrets to `/run/secrets/` but forgetting to configure `model_config = SettingsConfigDict(secrets_dir='/run/secrets')` in Pydantic, causing silent startup failures.
- 🚩 **Token Replay Vulnerability:** Implementing a Refresh Token Grace Period without tracking the **Token Family**, allowing hackers to replay stolen old tokens within the grace window.
- 🚩 **HPA Connection Paradox:** Relying solely on SQLAlchemy connection pooling in a Kubernetes HPA environment, leading to database connection exhaustion and fatal crashes when pods scale up. Must use PgBouncer or RDS Proxy.
- 🚩 **GitOps Race Condition:** Applying Migration Jobs and Deployments simultaneously in K8s without ArgoCD Sync Waves or Helm Hooks, causing them to run concurrently and crashing old pods.
- 🚩 **CORS Masking Trap:** Using FastAPI `CORSMiddleware` behind an Nginx proxy in production, causing 404/413/500 errors to lack CORS headers, deceiving the frontend with fake CORS errors.
- 🚩 **PITR Downtime Trap:** Relying exclusively on Managed Database PITR for data recovery, failing to realize it can take hours to restore. Use a Delayed Replica for instant failover.
- 🚩 **Mass-Logout DDoS:** Running a single-node Redis for Auth Token Families without HA or `appendfsync always`, causing a Thundering Herd DDoS on the Argon2id login API if Redis restarts.
- 🚩 **I/O Bottleneck:** Handling large file uploads (PDF, video) through the backend FastAPI workers instead of using Pre-signed URLs for direct S3 upload, exhausting worker I/O.
- 🚩 **Soft Delete DB Trap:** Using standard `UNIQUE` constraints (e.g., on emails) alongside a `deleted_at` soft delete column, causing IntegrityErrors when a deleted user tries to re-register.
- 🚩 **Supply Chain Attack:** Using `pip install -U` or raw `requirements.txt` in CI/CD without lockfiles (Poetry/uv) or hash pinning, opening the door to malicious dependency updates.
- 🚩 **Compliance Trap:** Dumping raw JSON request payloads into logs without a Redaction Middleware, leaking PII/PHI/Passwords into ELK/Datadog.
- 🚩 **TOCTOU Trap:** Using naive "Read-then-Update" transactions for financial/inventory operations without Pessimistic Locking (`SELECT FOR UPDATE`), allowing double-spending race conditions.
- 🚩 **Poison Pill Trap:** Running background task queues (Celery/ARQ) without a Dead Letter Queue (DLQ) or `max_retries`, allowing a crashing task to loop infinitely and consume all workers.
- 🚩 **Proxy IP Trap:** Relying on raw client IP or blindly trusting `X-Forwarded-For` for Rate Limiting behind a Load Balancer. Either blocks the LB IP entirely or allows attackers to spoof IPs. Must use `--forwarded-allow-ips`.
- 🚩 **SIGTERM Race Condition:** Deploying K8s Pods without a `preStop: sleep 5` hook. The app shuts down faster than kube-proxy updates its routes, dropping inflight requests and throwing 502 Bad Gateway errors during Rolling Updates.
- 🚩 **Deployment Downtime:** Attempting zero-downtime deployments via `docker-compose up -d` over SSH without a Blue/Green proxy or orchestrator.
- 🚩 **Weak Hashing:** Using standard `bcrypt` instead of `Argon2id` for highly sensitive systems.
- 🚩 **Pydantic V1 Syntax:** Using outdated `.dict()`, `class Config`, or legacy validators in Pydantic V2 environments. Always use `model_dump()` and `ConfigDict`.
- 🚩 **Secret Leakage:** Using `env_file: .env` in Docker Compose for production, which exposes secrets in container plaintext (e.g. `os.environ`).
- 🚩 **ASGI Worker Exhaustion:** Using the WSGI formula (`2 * cores + 1`) for ASGI workers, leading to RAM waste and Database Connection Pool exhaustion.
- 🚩 **Architecture Collapse:** Importing directly from `crud/` into `services/` without using Dependency Inversion via Interfaces.
- 🚩 **The Dead Volume Trap:** Mounting local code to a Docker container for development but forgetting to pass `--reload` to Uvicorn, making hot-reloading impossible.
- 🚩 **The Local CLI Leak:** Passing Redis or DB passwords via `--requirepass` in `docker-compose.yml`, building bad habits and risking parity drift with Production. Use a mounted config file instead.
- 🚩 **The Special Character Crash:** Using special characters (`@`, `/`) in DB passwords without URL-Encoding them. This breaks the URI parser in PgBouncer. Passwords must be Alphanumeric or URL-Encoded.
- 🚩 **The Grace Period Clash:** Setting Gunicorn timeout to 120s but forgetting to increase K8s `terminationGracePeriodSeconds` (default 30s). K8s will still SIGKILL the pod after 30s, rendering the Gunicorn timeout useless.
- 🚩 **The Entrypoint Permission Crash:** Using `runAsNonRoot: true` on the official `postgres` Docker image. The official image requires root at boot to `chown` the volume before it drops privileges itself.
- 🚩 **The Shell Interpolation Trap:** Using `sh -c "echo $(cat /secret/password)"` to build config files. If the password contains backticks or `$()`, the shell will execute them. Mount complete config files instead.
- 🚩 **The Log Exhaustion Trap:** Running Docker Compose environments without configuring log rotation (`max-size`, `max-file`). Logs will grow indefinitely and crash the host OS (Disk Pressure).

## Skill Output

When executed, this skill generates the following file structure:

```
.
├── backend/                 # FastAPI application
│   ├── app/                 # Application code
│   │   ├── api/             # API endpoints (v1)
│   │   │   ├── v1/          # Version 1 API
│   │   │   │   ├── api.py   # Main API router
│   │   │   │   ├── endpoints/
│   │   │   │   │   ├── auth.py      # Authentication endpoints
│   │   │   │   │   ├── users.py     # User management endpoints
│   │   │   │   │   └── cache_example.py  # Example cache usage
│   │   │   │   └── __init__.py
│   │   │   └── __init__.py
│   │   ├── core/            # Core configuration
│   │   │   ├── config.py    # Settings and configuration
│   │   │   └── __init__.py
│   │   ├── crud/            # Database operations (Implements interfaces)
│   │   │   ├── user.py      # User CRUD operations
│   │   │   └── __init__.py
│   │   ├── db/              # Database setup
│   │   │   ├── base_class.py  # Base model class
│   │   │   ├── session.py   # Database session management
│   │   │   └── __init__.py
│   │   ├── interfaces/      # Abstract Base Classes (Dependency Inversion)
│   │   │   ├── user_repository.py 
│   │   │   └── __init__.py
│   │   ├── models/          # SQLAlchemy models
│   │   │   ├── user.py      # User model
│   │   │   └── __init__.py
│   │   ├── schemas/         # Pydantic schemas
│   │   │   ├── token.py     # Token schemas
│   │   │   ├── user.py      # User schemas
│   │   │   └── __init__.py
│   │   ├── services/        # Business logic (placeholder)
│   │   │   └__init__.py
│   │   ├── utils/           # Utility functions
│   │   │   ├── security.py  # Password hashing, JWT handling
│   │   │   ├── redis.py     # Redis cache utility
│   │   │   └── __init__.py
│   │   └── __init__.py
│   ├── tests/               # Test files
│   │   ├── test_auth.py     # Authentication tests
│   │   └── test_redis.py    # Redis cache tests
│   ├── alembic/             # Database migrations
│   │   ├── env.py           # Alembic environment
│   │   ├── alembic.ini      # Alembic configuration
│   │   ├── script.py.mako   # Migration template
│   │   └── versions/        # Migration versions
│   │       └── 2c79c9c4413e_create_user_table.py
│   ├── Dockerfile           # Backend container definition
│   ├── requirements.txt     # Python dependencies
│   └── .env                 # Environment variables (generated from .env.example)
├── frontend/                # Static frontend files
│   └── index.html           # Placeholder frontend (React/Tailwind ready)
├── nginx/                   # Nginx configuration
│   ├── nginx.conf           # Main Nginx configuration
│   └── certs/               # SSL certificates directory (empty, for user to populate)
├── docker-compose.yml       # Service orchestration
├── .env.example             # Environment variables template
├── README.md                # Comprehensive documentation
└── backend-setup-skill.md   # This skill documentation
```

## Implementation Details

### Backend Architecture

1. **FastAPI Application** (`backend/app/main.py`)
   - Application factory pattern
   - CORS middleware configuration
   - API router inclusion
   - Health check endpoint

2. **Configuration** (`backend/app/core/config.py`)
   - Environment variable-based settings
   - Database connection building
   - Redis connection configuration
   - JWT configuration
   - CORS origins parsing

3. **Authentication System** (`backend/app/utils/security.py`)
   - Password hashing with bcrypt
   - JWT token creation (access/refresh)
   - Token decoding and validation
   - Password verification utilities

4. **Redis Cache Utility** (`backend/app/utils/redis.py`)
   - Redis client initialization
   - Connection pooling
   - Get/set/delete operations with TTL
   - Cache key generation helpers
   - Error handling and fallback logic

5. **Database Layer**
   - SQLAlchemy models (`backend/app/models/user.py`)
   - CRUD operations (`backend/app/crud/user.py`)
   - Database session management (`backend/app/db/session.py`)
   - Alembic migrations for schema versioning

6. **API Endpoints**
   - Authentication: `/api/v1/auth/login/access-token` and `/api/v1/auth/login/refresh-token`
   - Users: `/api/v1/users/` (CRUD operations)
   - Cache example: `/api/v1/cache/example/` (demonstrates Redis usage)
   - Automatic API documentation via Swagger UI and ReDoc

### Infrastructure

1. **Docker Setup**
   - Multi-service docker-compose.yml
   - Backend Dockerfile with optimized Python image
   - PostgreSQL service with healthcheck
   - Redis service with healthcheck and security configuration
   - Nginx service for reverse proxy and static serving
   - Volume mounts for development convenience

2. **Nginx Configuration**
   - HTTP to HTTPS redirect
   - SSL termination (certificates to be provided by user)
   - Static file serving for frontend
   - API proxying to backend service
   - Security headers implementation
   - Health check endpoint

3. **Security Implementation**
   - Environment-based secrets (never hardcoded)
   - Strong password hashing (bcrypt)
   - JWT with configurable expiration
   - CORS with configurable origins
   - SQL injection prevention via SQLAlchemy ORM
   - Input validation via Pydantic
   - Redis security (password protection, network binding, command restrictions)
   - Security headers implemented in Nginx:
     - X-Frame-Options: SAMEORIGIN
     - X-XSS-Protection: 1; mode=block
     - X-Content-Type-Options: nosniff
     - Referrer-Policy: no-referrer-when-downgrade
     - Content-Security-Policy: restrictive policy
   - Environment-based configuration prevents accidental credential commits
   - No privileged containers or unnecessary capabilities in Docker

## Prerequisites

Before running this skill, ensure you have:

- Docker and Docker Compose installed and running
- Git (optional, for version control)
- Approximately 2GB of free disk space
- Ports 80, 443, 6379 (Redis), and 8000 available on your host machine

## Usage Instructions

1. **Execute the Skill**
   Run this skill in an empty directory:

   ```
   /backend-setup-skill
   ```

2. **Configure Environment**

   ```bash
   cp .env.example .env
   # Edit .env with your specific values:
   # - Change SECRET_KEY to a strong random value
   # - Adjust database credentials if needed
   # - Set REDIS_PASSWORD to a strong random value
   # - Configure CORS origins for your frontend
   # - Set proper JWT expiration times
   ```

3. **SSL Certificates (Production)**
   For production HTTPS:

   ```
   # Place your SSL certificate and key in:
   ./nginx/certs/fullchain.pem
   ./nginx/certs/privkey.pem
   # Update paths in nginx/nginx.conf if using different filenames
   ```

   For development, you can:
   - Use self-signed certificates
   - Or modify nginx/nginx.conf to remove SSL configuration and use HTTP only

4. **Start Services**

   ```bash
   docker-compose up --build
   ```

5. **Verify Installation**
   - Frontend: http://localhost (shows placeholder)
   - Backend API: http://localhost/api
   - API Documentation: http://localhost/api/docs (Swagger UI)
   - Alternative Docs: http://localhost/api/redoc (ReDoc)
   - Health Check: http://localhost/health
   - Database: Accessible at localhost:5432 with credentials from .env
   - Redis: Accessible at localhost:6379 with password from .env

## Development Workflow

### Backend Development

- Modify code in `backend/app/` directory
- Changes are reflected immediately due to volume mounting in docker-compose
- Run tests: `docker-compose exec backend pytest`
- Create migrations:
  ```bash
  docker-compose exec backend alembic revision --autogenerate -m "description"
  docker-compose exec backend alembic upgrade head
  ```

### Frontend Development

- Replace `frontend/index.html` with your React/Tailwind application
- The nginx configuration serves static files from the frontend directory
- For React development, you may want to proxy API requests to backend

### Database Management

- Initial migration is created automatically
- To create new migrations:
  ```bash
  docker-compose exec backend alembic revision --autogenerate -m "description"
  ```
- To apply migrations:
  ```bash
  docker-compose exec backend alembic upgrade head
  ```

### Redis Usage Examples

The skill includes an example cache utility and endpoint:

- Use `backend/app/utils/redis.py` for caching operations
- Example endpoint: `GET /api/v1/cache/example/` demonstrates caching
- Common patterns:

  ```python
  # Cache a value for 5 minutes
  await redis_client.setex("user:123:profile", 300, json.dumps(user_data))

  # Get a cached value
  cached_data = await redis_client.get("user:123:profile")

  # Delete a cache entry
  await redis_client.delete("user:123:profile")
  ```

## Security Considerations

### Critical Security Actions Required Before Production

1. **Change SECRET_KEY**: Generate a strong random value (at least 32 characters)
2. **Use Strong Passwords**: Update POSTGRES_PASSWORD and REDIS_PASSWORD
3. **Configure Proper CORS**: Restrict BACKEND_CORS_ORIGINS to your actual domains
4. **Enable HTTPS**: Obtain and install proper SSL certificates
5. **Update JWT Expirations**: Consider shorter access token lifetimes for high-security applications
6. **Redis Security**:
   - Ensure Redis is bound to internal networks only (not 0.0.0.0)
   - Set a strong REDIS_PASSWORD in .env
   - Verify dangerous commands are restricted in production
   - Set appropriate memory limits for Redis
   - Configure Redis persistence correctly (RDB/AOF) based on use case
7. **Environment Separation**: Use different .env files for development, staging, and production

### Built-in Security Features

- Passwords hashed with bcrypt (work factor appropriate for current hardware)
- JWT tokens signed with HMAC-SHA256 using SECRET_KEY
- Access tokens expire (configurable, default 60 minutes)
- Refresh tokens expire (configurable, default 30 days)
- SQL injection prevention via SQLAlchemy ORM
- Input validation and sanitization via Pydantic models
- CORS middleware with configurable origins
- Redis protected by password and network binding
- Security headers implemented in Nginx:
  - X-Frame-Options: SAMEORIGIN
  - X-XSS-Protection: 1; mode=block
  - X-Content-Type-Options: nosniff
  - Referrer-Policy: no-referrer-when-downgrade
  - Content-Security-Policy: restrictive policy
- Environment-based configuration prevents accidental credential commits
- No privileged containers or unnecessary capabilities in Docker

## Customization Guidelines

### Adding New API Versions

1. Create new directory: `backend/app/api/v2/`
2. Copy structure from v1: endpoints, schemas, etc.
3. Update `backend/app/api/v1/api.py` to include new version
4. Add version prefix in `backend/app/main.py` or create separate router

### Adding New Models

1. Create model in `backend/app/models/`
2. Create corresponding schema in `backend/app/schemas/`
3. Implement CRUD operations in `backend/app/crud/`
4. Create endpoints in `backend/app/api/v1/endpoints/`
5. Generate migration: `alembic revision --autogenerate`
6. Apply migration: `alembic upgrade head`

### Extending Redis Usage

1. Add more cache utilities in `backend/app/utils/redis.py`
2. Create specialized cache services in `backend/app/services/`
3. Implement distributed locking with Redis for race condition prevention
4. Use Redis Pub/Sub for real-time notifications between services
5. Add Redis monitoring and metrics collection

### Modifying Nginx Configuration

- Edit `nginx/nginx.conf` for:
  - Additional server blocks (subdomains, etc.)
  - Different SSL certificate paths
  - Custom routing rules
  - Rate limiting or authentication additions
  - WebSocket support configuration
  - Logging format adjustments
  - **Performance (The C10K Exhaustion Trap):** Nginx Ingress or local Nginx configs MUST define the `events { worker_connections 10240; }` block. Omitting this defaults to 512 connections, causing `Too many open files` and `502 Bad Gateway` when K8s scales up the backend.
  - **Payload Size (The JWT Buffer Overflow):** Nginx has a strict 4KB/8KB default for headers. If your JWT token grows, Nginx will block the request with 400 or 502 before it reaches FastAPI. You MUST add `client_header_buffer_size 16k;`, `large_client_header_buffers 4 32k;`, and `proxy_buffer_size 16k;` to your Nginx config.

### Extending Docker Setup

- Differentiate Development and Production: Use `Dockerfile.dev` for live-reloading (via Uvicorn `--reload`) and a multi-stage `Dockerfile.prod` for optimized, small-footprint production images.
- Enforce Environment Consistency (The Environment Schizophrenia): Dev, CI, and Prod MUST run on identical versions of Python (e.g. `python:3.12-slim`) and PostgreSQL (e.g. `postgres:15`).
- Supply Chain Security (The Lockfile): NEVER use a bare `requirements.txt`. You MUST generate a hash-pinned lockfile and install dependencies using `pip install --require-hashes -r requirements.txt` across all environments (Dev, CI, Prod). *Critical (The CI/CD Dependency Trap):* Test and Dev dependencies (like `pytest`, `black`) MUST also be hashed in a separate `requirements-dev.txt` to prevent CI/CD supply chain hijacking.
- Process Manager (The Single-Worker Trap): In Production, `uvicorn` does not spawn multiple workers natively when provided with the `WEB_CONCURRENCY` K8s env var. You MUST run FastAPI via Gunicorn: `CMD ["gunicorn", "app.main:app", "-k", "uvicorn.workers.UvicornWorker"]`. *Critical (The Silent Kill Trap):* Gunicorn will kill workers that take longer than 30 seconds to process a request (like PDF generation or 3rd-party API calls). You MUST configure `--timeout 120` and `--keep-alive 5`.
- Immutable Codebase (The RCE Trap): NEVER run `chown -R appuser:appgroup /app` on the source code. The code MUST belong to `root:root` and be Read-Only to the runtime user to prevent Backdoor installation if RCE occurs. *Critical (The Read-Only `__pycache__` Trap):* Because the codebase is read-only, Python and Gunicorn will crash when trying to write bytecode or temp files. You MUST set `ENV PYTHONDONTWRITEBYTECODE=1` and append `--worker-tmp-dir /dev/shm` to Gunicorn.
- Enforce Non-Root Execution: Ensure the `Dockerfile` creates and switches to a non-root `appuser` before `CMD` execution.
- Add services to docker-compose.yml (caching, queues, Celery workers). *Critical (The Missing Proxy Trap):* You MUST include PgBouncer in `docker-compose.yml` and force the backend to connect through it, mirroring the exact K8s Production Architecture. Otherwise, Developers will write code that breaks on Production Transaction Pooling. *Critical (The Local DDL Crash):* When local PgBouncer is running in Transaction Mode, running `alembic upgrade head` from inside the backend container will crash. You MUST provide a `SYNC_DATABASE_URL` (direct connection to DB) to the backend and configure `env.py` to use it for migrations.
- Set up secret management: **Production Secrets (Critical):** NEVER use `env_file: .env` to pass sensitive secrets (like `SECRET_KEY` or `POSTGRES_PASSWORD`) into production containers, as this exposes them to plaintext `os.environ` leaks via SSRF/RCE. Use Docker Secrets (mounted at `/run/secrets/`) or an external Vault (AWS Secrets Manager). *Warning:* Pydantic V2 BaseSettings defaults to reading `os.environ`. You MUST explicitly configure `model_config = SettingsConfigDict(secrets_dir='/run/secrets')` so Pydantic can map the mounted files into variables. *Critical (The K8s Secret Leak):* In K8s, NEVER use `envFrom: secretRef`. It unpacks K8s Secrets back into plaintext environment variables, defeating the entire purpose. You MUST use `volumeMounts` to mount Secrets as read-only files.

### Kubernetes (K8s) Deployment Architecture

When scaling beyond a single instance or managing high availability:

1. **Deployments:** Manage FastAPI replica sets. Configure Rolling Updates to ensure zero-downtime deployments. Set `strategy.rollingUpdate.maxSurge` and `maxUnavailable`.
2. **Auto-scaling:** Use Horizontal Pod Autoscaler (HPA) to scale backend pods based on CPU/Memory usage. *Critical (The Flapping Syndrome):* K8s HPA reacts instantly to micro-bursts, causing Pods to be created and destroyed rapidly (Flapping). You MUST configure a `behavior.scaleDown.stabilizationWindowSeconds` of at least 300 seconds to prevent dropped requests during iptables updates.
3. **Database (StatefulSets):** Deploy Postgres and Redis as StatefulSets with persistent volumes. *Critical (The Probe Collision):* NEVER use `livenessProbe` for Stateful Databases like Postgres or Redis. Long checkpoints will cause K8s to `SIGKILL` the container, leading to WAL/AOF file corruption. Use `startupProbe` and `readinessProbe` only. *Critical (The YAML Bash Escape):* NEVER pass passwords to Database pods using `command: ["sh", "-c", "echo $PASSWORD > file"]` in YAML. It causes Shell Injection and exposes secrets. Mount the K8s Secret directly as a config file (`/etc/redis/redis.conf`).
4. **Safe Migrations (Pre-Deploy Jobs):** Never run Alembic migrations in an `InitContainer` during a Deployment's Rolling Update. Migrations MUST run as an isolated **K8s Job** that completes BEFORE the Rolling Update begins. *Critical (The Immutable Job Crash):* K8s Jobs are immutable. If CI/CD runs `kubectl apply -f migration-job.yaml` a second time, it will throw an error and break the pipeline. You MUST delete the old job first (`kubectl delete job backend-db-migration --ignore-not-found`) before applying the new one, or use Helm hashes. *Critical (The DDL Transaction Pool Trap):* If you use PgBouncer in `transaction` mode, Alembic DDL commands will fail. The Migration Job MUST bypass PgBouncer and connect directly to Postgres.
5. **Services & Ingress:** Expose the backend via ClusterIP Services, and use an Ingress Controller (Nginx Ingress) for SSL termination, path-based routing, and load balancing. *Critical (The CORS Latency Trap):* Browsers send OPTIONS preflight requests before POST/PUT/DELETE. If not cached, API latency doubles. You MUST add `nginx.ingress.kubernetes.io/cors-max-age: "86400"` to the Ingress annotations.
6. **Secret Management & ps Leak (The Plaintext Dangers):** Never store raw Base64 secrets in `config.yaml`. *Critical (The `ps -ef` Leak):* When using DB CLI tools (like `redis-cli -a` or `redis-server --requirepass`) in K8s YAML, the passwords will be exposed in plaintext to anyone running `ps aux` in the container/node. You MUST use environment variables (e.g., `REDISCLI_AUTH`) or config files for passing passwords.
7. **StatefulSets, Ephemeral Redis & HA:** Use StatefulSets with Persistent Volume Claims (PVC) for databases and Redis. *Critical (The Ephemeral Trap):* If Redis runs as a Deployment without a PVC and gets restarted, all JWT Token Families and Rate Limit states are wiped out. Ensure Redis uses `--appendonly yes`. *Note (Redis HA):* For true Enterprise High Availability to avoid a Single Point of Failure (SPOF) during node maintenance, it is **RECOMMENDED** to use a managed Redis or a Helm Chart (e.g., `bitnami/redis-cluster`), instead of a raw 1-replica StatefulSet. *Critical (The Init Corruption Trap):* When PostgreSQL initializes a new blank volume, `initdb` can take 20s+ on slow cloud disks. If you only use `livenessProbe`, K8s will think it's dead at 15s and kill it, permanently corrupting the volume. You MUST configure a `startupProbe` with a long timeout for DB StatefulSets. *Critical (The fsGroup Permission Denied):* If you run DBs as `runAsNonRoot: true`, you MUST add `fsGroup: <uid>` to the `PodSecurityContext`, otherwise K8s will mount the PVC as root and the DB will crash with Permission Denied.
8. **QoS Auto-scaling & Auth Memory (The Login DoS Trap):** Enforce QoS Guaranteed (`requests.cpu == limits.cpu`) to prevent wasteful HPA scaling. *Critical (The Login DoS Trap):* Password hashing algorithms like Argon2id are intentionally memory-hard (~100MB per hash). If `limits.memory` is too low (e.g., 512Mi), 4 concurrent logins will OOMKill the backend Pod. You MUST provision at least 1Gi memory limits for Auth Pods or strictly rate-limit the `/login` endpoint concurrency.
9. **Root Privilege Escalation (The RCE Trap):** Docker and K8s containers run as root (UID 0) by default. If a Python package gets compromised via RCE, hackers gain root access to the container and can easily escape to the Node. You MUST enforce `securityContext: {runAsNonRoot: true, allowPrivilegeEscalation: false}` on all deployments (Backend, DB, Redis, Jobs).
10. **Deterministic Rollbacks (The :latest Illusion):** NEVER use the `:latest` tag in Production Deployments. `kubectl rollout undo` only reverts the K8s manifest. If the manifest still says `:latest`, K8s will re-pull the broken image. You MUST pin images to specific Git Commit SHAs or semantic versions (e.g., `backend:a1b2c3d`).
11. **PgBouncer Authentication (The SCRAM Blindspot):** Postgres 15+ defaults to `scram-sha-256` password encryption. When deploying PgBouncer in front of it, you MUST explicitly configure PgBouncer (e.g., `AUTH_TYPE: scram-sha-256`), otherwise Backend authentication will fail.
12. **Asyncpg & PgBouncer (The Prepared Statement Crash):** `asyncpg` uses Prepared Statements by default. PgBouncer in `transaction` mode does NOT support Prepared Statements across physical connections. You MUST disable it in SQLAlchemy (`connect_args={"prepared_statement_cache_size": 0}`).
13. **Ingress Client IPs (The CIDR Blindspot):** Nginx Ingress will overwrite `X-Forwarded-For` with internal K8s IPs unless configured properly. You MUST enable `use-forwarded-headers: "true"` in the Nginx Global ConfigMap, and set `--forwarded-allow-ips="*"` in Uvicorn so FastAPI trusts the Ingress proxy.

### CI/CD Pipelines (GitHub Actions & Jenkins)

1. **Linting and Testing:** Run `black`, `flake8`, `isort`, `bandit` (for security), and `pytest` with `pytest-asyncio`. Ensure tests run in a clean environment mirroring production. *Critical (The CI Race Condition):* When using `--health-cmd pg_isready` for Postgres services in CI/CD, you MUST specify the user (`pg_isready -U postgres`), otherwise the healthcheck will run as the runner's user, fail randomly, and cause Flaky Tests.
2. **Unit & Integration Testing:** Run `pytest`. Enforce code coverage thresholds (e.g., >80%).
3. **Security Scanning:** Run `bandit` (Python security analysis) and `trivy` (Container vulnerability scanning).
4. **Build & Push:** Build the Docker image, tag it with the commit SHA, and push to a registry (Docker Hub, ECR, GCR).
5. **Deploy:** Deploy to K8s (`kubectl apply` or Helm upgrade) or use Docker Swarm / Nomad. *Warning: Never use standard `docker-compose up` over SSH for production updates, as it causes inevitable network downtime. If not using an orchestrator, implement Blue/Green deployment at the Nginx reverse proxy level.*

**GitHub Actions Example:** Use workflow triggers on `push` to `main` and `pull_request`. Utilize environments for manual approval steps before production deployment.
**Jenkins Example:** Use declarative pipelines (`Jenkinsfile`). Leverage Jenkins credentials store for secrets and Jenkins agents for distributed builds. Ensure pipeline definitions are tracked in version control.

## Troubleshooting Guide

### Common Issues and Solutions

**1. Containers Fail to Start**

- Check logs: `docker-compose logs [service]`
- Verify port availability: `netstat -tulpn | grep LISTEN`
- Ensure sufficient disk space and memory
- Validate docker-compose.yml syntax

**2. Database Connection Issues**

- Wait for db healthcheck: `docker-compose ps db` should show "healthy"
- Verify POSTGRES\_\* environment variables in .env
- Check network connectivity: `docker-compose exec backend ping db`
- Ensure database service is started before backend (depends_on with condition)

**3. Redis Connection Issues**

- Wait for redis healthcheck: `docker-compose ps redis` should show "healthy"
- Verify REDIS_PASSWORD in .env matches Redis config
- Check network connectivity: `docker-compose exec backend ping redis`
- Ensure Redis service is started before backend (depends_on with condition)
- Verify Redis is bound to correct network interface

**4. Authentication Problems**

- Verify SECRET_KEY is consistent across services
- Check token expiration settings
- Ensure bcrypt is properly installed (in requirements.txt)
- Validate password hashing/matching logic

**5. SSL/TLS Issues**

- Confirm certificate files exist in nginx/certs/
- Verify certificate validity: `openssl x509 -in nginx/certs/fullchain.pem -text -noout`
- Check nginx error logs: `docker-compose logs nginx`
- Test SSL configuration: `openssl s_client -connect localhost:443 -servername localhost`

**6. CORS Issues**

- Verify BACKEND_CORS_ORIGINS matches frontend origin
- Check browser console for CORS error details
- Ensure credentials are included when needed (withCredentials: true)
- Validate preflight requests are handled correctly

### Performance Optimization

- Adjust worker counts in Dockerfile/production settings
- Configure database connection pooling
- Implement caching layer (Redis) for frequent queries
- Add CDN for static frontend assets
- Enable gzip compression in Nginx
- Consider read replicas for heavy read workloads
- Optimize Redis memory usage and eviction policies
- Use Redis pipelines for batch operations

## Testing

### Running Tests

```bash
# Run all tests
docker-compose exec backend pytest

# Run specific test file
docker-compose exec backend pytest tests/test_auth.py
docker-compose exec backend pytest tests/test_redis.py

# Run tests with coverage
docker-compose exec backend pytest --cov=app --cov-report=term-missing
```

### Comprehensive Test Scenarios (Writing Tests)

- **Async Testing Strategy (Critical)**:
  - You MUST install and use `pytest-asyncio` to test FastAPI async routes and `asyncpg` queries.
  - Standard `pytest` is synchronous. If you do not configure an async test runner and proper async fixtures, database calls will crash with "Task attached to a different loop".
  - **The Dependency Injection Trap:** When using `TestClient` or `AsyncClient`, FastAPI's dependency injection will spawn a *new* DB connection for the API, bypassing your test's rollback mechanism and committing test data to the DB.
  - **Solution (Nested Transactions):** You must force `pytest-asyncio` to share a single event loop, create a Savepoint (nested transaction) for each test, and override `get_db` to force the API to use the test's session.
  
  <details>
  <summary><b>View `conftest.py` Blueprint</b></summary>
  
  ```python
  import pytest
  import pytest_asyncio
  import asyncio
  from sqlalchemy import event
  from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
  from httpx import AsyncClient
  from app.db.session import get_db
  from app.main import app
  
  TEST_DB_URL = "postgresql+asyncpg://user:pass@localhost:5432/test_db"
  engine = create_async_engine(TEST_DB_URL, echo=False)
  
  @pytest.fixture(scope="session")
  def event_loop():
      """Force all test cases to share the same Async Event Loop to prevent SQLAlchemy crashes."""
      loop = asyncio.get_event_loop_policy().new_event_loop()
      yield loop
      loop.close()
  
  @pytest_asyncio.fixture(scope="function")
  async def db_session():
      """Create a Savepoint (Nested Transaction) for each test and rollback after completion."""
      async with engine.connect() as connection:
          transaction = await connection.begin()
          async_session = AsyncSession(bind=connection, expire_on_commit=False)
          
          await connection.begin_nested()
  
          @event.listens_for(async_session.sync_session, "after_transaction_end")
          def end_savepoint(session, transaction):
              if transaction.nested and not transaction._parent.nested:
                  connection.sync_connection.begin_nested()
  
          yield async_session
  
          await async_session.close()
          await transaction.rollback()
  
  @pytest_asyncio.fixture(scope="function")
  async def client(db_session):
      """Override FastAPI's Dependency Injection to force the API to use the test's Savepoint."""
      def override_get_db():
          yield db_session
  
      app.dependency_overrides[get_db] = override_get_db
      
      async with AsyncClient(app=app, base_url="http://test") as ac:
          yield ac
          
      app.dependency_overrides.clear()
  ```
  </details>

- **Unit Testing Scenarios**:
  - Place test files in `backend/tests/` directory.
  - Test pure business logic functions (e.g., tax calculation, password strength validation) without database or network dependencies.
  - Mock database sessions and Redis clients to test service/crud layer functions in isolation.
  - Test JWT token generation, parsing, and failure on malformed/expired tokens.

- **Integration Testing Scenarios**:
  - Use `TestClient` (FastAPI) and an actual test database (Warning: Never use SQLite in-memory for this stack. It does not support `asyncpg`, `JSONB`, or table partitioning. You MUST use a temporary PostgreSQL instance via Docker Compose or `Testcontainers`).
  - Use pytest fixtures to seed the database and provide authenticated API clients (e.g., `client_user_token`, `client_admin_token`).
  - **Auth Flow**: Complete cycle of user registration, login (retrieving JWT), and accessing a protected `/me` route.
  - **CRUD Operations**: Test Create, Read, Update, and Delete on a model, verifying the database state changes correctly.
  - **Permission Enforcement**: Ensure a standard user receives 403 Forbidden when attempting an admin-only action.

- **Caching & Async Scenarios**:
  - Test Redis operations (set, get, delete, TTL expiration).
  - Verify cache invalidation triggers properly when database records are updated.
  - Test background task enqueuing (e.g., ensuring an email task is added to Celery queue upon registration).

- **Failure & Edge Cases**:
  - Assert appropriate HTTP status codes (e.g., 400 for bad input, 404 for not found, 422 for schema validation errors, 401 for bad auth).
  - Test missing required fields, extremely long strings, and invalid data formats to verify Pydantic's rejection.
  - Simulate database connection failures (if mocking) to ensure generic exceptions don't leak stack traces (return safe 500s).

## Maintenance

### Regular Updates

1. Update Python dependencies:
   ```bash
   # Warning (Supply Chain Attack): NEVER use `pip install -U` or unpinned `requirements.txt` in production CI/CD. 
   # You MUST use a deterministic package manager (Poetry, uv, pip-tools) with a Lockfile and Hash Pinning.
   # docker-compose exec backend uv sync # (or poetry install)
   ```
2. Update base images:
   ```bash
   docker-compose pull
   docker-compose up --build
   ```
3. Monitor security advisories for:
   - FastAPI/Uvicorn
   - PostgreSQL
   - Redis
   - Nginx
   - Python cryptography libraries

### Backup Strategy

1. **Managed Databases (Recommended for Production):** Do not run self-hosted databases in containers for production. Use Managed Services (AWS RDS, GCP Cloud SQL, Supabase) to automate Backups, Point-In-Time Recovery (PITR), and failover. *Critical (PITR Downtime Trap):* Restoring from a PITR snapshot for a large database can take many hours, causing massive downtime. For mission-critical data, you MUST configure a **Delayed Replica** (a read replica lagging 1-2 hours behind the master). In a logic disaster (e.g. accidental bulk update), promote the Delayed Replica to Master for near-instant recovery.
2. **Local/Dev Database Backups (pg_dump):**
   ```bash
   # Export database
   docker-compose exec db pg_dump -U $POSTGRES_USER $POSTGRES_DB > backup.sql

   # Import database
   cat backup.sql | docker-compose exec -i db psql -U $POSTGRES_USER $POSTGRES_DB
   ```

2. Configuration backup: .env file (store securely)
3. Persistent data: postgres_data and redis_data volumes (managed by Docker)
4. Redis RDB/AOF persistence files if configured

## License and Usage

This skill generates code that is free to use, modify, and distribute. The generated backend follows standard open-source practices and can be adapted for commercial, private, or open-source projects.

**Note**: Always review and adjust security configurations for your specific use case before deploying to production. The generated code provides a secure foundation but requires proper configuration and ongoing maintenance to remain secure.

---

_Skill version: 1.1.0_
_Last updated: 2026-08-29_
\*Compatible with: Python 3.9+, FastAPI 0.68+, PostgreSQL 13+, Redis 7.0+, Docker 20.10+, Nginx 1.20+
