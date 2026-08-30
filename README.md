# Advanced Secure Backend Setup (Battle-Hardened Edition)

This repository contains a **Battle-Hardened, Enterprise-Grade** backend boilerplate built with Python/FastAPI, PostgreSQL (async), Redis, Docker, and Kubernetes. 

Unlike standard tutorials, this architecture has been meticulously engineered to mitigate severe real-world production traps: Connection Pool Deadlocks, K8s Flapping, OOMKilled Signals, JWT Buffer Overflows, and CI/CD Supply Chain Attacks.

---

## 🌟 Architecture & Hardened Features

### 1. High-Performance Database & Connection Pooling
- **PgBouncer (Transaction Pooling)**: Integrated natively (both Local and Prod) to prevent the K8s HPA Connection Paradox. Handles thousands of concurrent FastAPI pods without crashing PostgreSQL.
- **SQLAlchemy NullPool**: FastAPI explicitly uses `poolclass=NullPool` to yield physical connection management entirely to PgBouncer, eliminating Pool-on-Pool deadlocks.
- **Prepared Statement Safety**: Asyncpg's prepared statements are strictly disabled at the driver level to prevent crashes when PgBouncer multiplexes transactions.
- **Primary Keys & Soft Deletion**: Uses UUIDv7/ULID for time-sorted locality. Soft deletion (`deleted_at`) uses PostgreSQL Partial Unique Indexes to prevent `IntegrityError` DB Traps.

### 2. State-of-the-Art Security & Defense-in-Depth
- **Zero CLI Leakage**: Redis and PostgreSQL passwords are never passed via CLI arguments or `envFrom`. Secrets are directly mounted into files (`/run/secrets/` and `/tmp/redis.conf`) to prevent `ps aux` and `os.environ` leaks.
- **Read-Only Codebase**: Production Docker images enforce Read-Only root filesystems (`ro`). Python is configured with `PYTHONDONTWRITEBYTECODE=1` and Gunicorn temp files are routed to `/dev/shm` (RAM).
- **Token Family Idempotency**: JWT Refresh tokens are backed by Redis with a Grace Period and Branching Detection to mitigate Token Replay attacks and Mass-Logout DDoS.
- **CI/CD Supply Chain Armor**: GitHub Actions strict dependency installation (`pip install --require-hashes`) completely blocks malicious PyPI package injections during build time.

### 3. Advanced K8s Orchestration & Resilience
- **Gunicorn ASGI Management**: Uvicorn is strictly managed by Gunicorn (`-k uvicorn.workers.UvicornWorker`). `WEB_CONCURRENCY` dynamically calculates workers based on CPU limits to prevent Cgroup CPU Illusions (OOMKilled).
- **Synchronized Grace Periods**: Gunicorn timeouts (`120s`) and Kubernetes `terminationGracePeriodSeconds` (`130s`) are perfectly synchronized with a `preStop` hook to guarantee zero-downtime rolling updates without SIGTERM Race Conditions.
- **Probe Collision Safety**: Kubernetes `/health/liveness` (shallow) and `/health/readiness` (deep) probes are strictly separated to prevent DB checkpoint stutters from causing a Full Pod Outage.
- **HPA Flapping Defense**: Kubernetes HPA uses `stabilizationWindowSeconds: 300` to prevent network jitter scaling crashes.

### 4. Edge Proxy & Network Robustness
- **Nginx JWT Buffer Overflow Protection**: `large_client_header_buffers` is expanded to safely accommodate massive JWT tokens (OIDC/Role claims) without throwing silent HTTP 400 errors.
- **C10K Nginx Tuning**: Worker connections and epoll configurations are optimized to handle 10,000+ concurrent connections.
- **Log Exhaustion Protection**: Docker Compose environments enforce JSON file log rotation (`max-size: 10m`) to prevent Staging/Local disk pressure crashes.

---

## 📂 Project Structure

```text
.
├── backend/                 # FastAPI application
│   ├── app/                 # Source Code
│   │   ├── api/             # API Router & Endpoints
│   │   ├── core/            # Config & Pydantic BaseSettings
│   │   ├── crud/            # Repository Implementations
│   │   ├── db/              # Async Engine & SessionMaker
│   │   ├── interfaces/      # ABCs for Dependency Inversion
│   │   ├── models/          # SQLAlchemy 2.0 Entities
│   │   ├── schemas/         # Pydantic V2 DTOs
│   │   ├── services/        # Business Logic Layer
│   │   └── utils/           # Redis & Argon2 Security Helpers
│   ├── tests/               # Pytest async test suite
│   ├── alembic/             # Database migrations
│   ├── Dockerfile.dev       # Dev container with Uvicorn Hot-Reloading
│   ├── Dockerfile.prod      # Multi-stage Prod container (Gunicorn + Read-Only)
│   └── requirements.txt     # Hash-pinned dependencies
├── k8s/                     # Kubernetes Manifests
│   ├── backend.yaml         # Deployment, Service, HPA (Grace Period Synced)
│   ├── database.yaml        # Bitnami/Postgres StatefulSet + PgBouncer
│   ├── ingress.yaml         # Nginx Ingress Controller config
│   ├── redis.yaml           # Redis StatefulSet (Secret File Mounted)
│   ├── config.yaml          # ConfigMaps and Secrets
│   ├── migration-job.yaml   # Immutable DB Schema CI/CD Migration Job
│   └── namespace.yaml       
├── frontend/                # Static frontend deployment target
├── nginx/                   # Nginx reverse proxy configuration (C10K + JWT Buffer)
├── docker-compose.yml       # Local dev with exact Prod Parity (PgBouncer, Log Rotation)
├── .env.example             # Environment variables template
├── TROUBLESHOOTING.md       # Guide for DB URL-Encoding & Advanced Errors
├── SKILL.md                 # Complete Architectural Rules & Design Patterns
└── README.md                # This documentation
```

---

## 🚀 Getting Started

### Local Development (Docker Compose)

The local setup is designed to mirror production networking perfectly, including PgBouncer, Redis Config files, and Log Rotation.

1. **Configure Environment**:
   ```bash
   cp .env.example .env
   # Edit .env with your local values. 
   # WARNING: DB Passwords must be Alphanumeric or URL-Encoded (See TROUBLESHOOTING.md)
   ```

2. **Start Services**:
   ```bash
   docker-compose up -d --build
   ```

3. **Access Services**:
   - API Endpoint: `http://localhost/api`
   - Swagger UI: `http://localhost/api/docs`
   - ReDoc: `http://localhost/api/redoc`

### Migrations (Alembic)

Due to PgBouncer Transaction Mode, schema DDL migrations use a dedicated Sync connection:
```bash
docker-compose exec backend alembic revision --autogenerate -m "migration_name"
docker-compose exec backend alembic upgrade head
```

### Running Tests (Pytest)

The test suite uses `pytest-asyncio` with nested transactions (Savepoints).
```bash
docker-compose exec backend pytest tests/
```

---

## 🚢 Production Deployment (Kubernetes)

The `/k8s` directory contains the production-ready manifests.

1. **Secrets**: Review and update `k8s/config.yaml` with production secrets.
2. **Push Image**: Ensure you have built and pushed the `backend:latest` image to your registry.
3. **Migrate DB**: CI/CD must delete the old immutable migration Job before applying:
   ```bash
   kubectl delete job backend-db-migration -n backend-prod --ignore-not-found
   kubectl apply -f k8s/migration-job.yaml
   ```
4. **Deploy System**:
   ```bash
   kubectl apply -f k8s/
   ```

---

## 📚 Documentation & Guidelines

Before making any modifications to the architecture, you **MUST** read:
1. `SKILL.md`: Details the Red Flags, Architectural Patterns, and why certain decisions (like Gunicorn, PgBouncer, NullPool) are mandatory.
2. `TROUBLESHOOTING.md`: Contains fixes for URL-Encoding crashes and database connection issues.
