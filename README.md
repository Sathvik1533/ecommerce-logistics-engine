# E-Commerce Logistics Engine

A modular backend platform engine built for global e-commerce logistics, fulfillment management, and transactional inventory reservations.

---

## 1. Project Purpose & Domain

The **E-Commerce Logistics Engine** serves as the backbone for international fulfillment operations. The platform coordinates high-volume order ingestion, validates inventory availability across regional fulfillment centers, guarantees atomic stock reservation to prevent overselling, and orchestrates asynchronous post-order processing (notification dispatches, warehouse picking allocations, carrier tracking).

---

## 2. Architecture & Vertical Slice Rationale

The repository is built as a **Modular Monolith** employing **Vertical Slice Architecture (VSA)**:

```
app/
├── core/                   # Cross-cutting infrastructure (config, database engine, sessions)
├── features/               # Business capabilities organized as vertical slices
│   ├── orders/             # Order creation, status tracking, line item models & schemas
│   └── inventory/          # Warehouse stock allocation, locking & reservation boundaries
├── workers/                # Celery background workers and asynchronous task definitions
```

### Why Vertical Slice Architecture?
- **Business Cohesion:** Rather than splitting an order feature across unrelated horizontal directories (`controllers/`, `services/`, `repositories/`), all code related to `orders` lives in `app/features/orders/`.
- **Low Coupling:** Slices interact via well-defined interface contracts (`OrderServiceInterface`, `InventoryServiceInterface`), preventing tight internal coupling and spaghetti dependencies.
- **Maintainability & Evolution:** Isolated slices allow independent refactoring and ease potential future extraction into dedicated microservices without premature architectural fragmentation.

Detailed sequence diagrams, transaction boundaries, and concurrency strategies are documented in [`docs/architecture.md`](docs/architecture.md).

---

## 3. Technology Choices & Technical Trade-offs

| Component | Technology | Rationale & Trade-offs |
| :--- | :--- | :--- |
| **Language** | Python 3.11 | High performance via CPython optimizations, native `StrEnum`, strict typing with Pydantic v2. |
| **API Framework** | FastAPI | High async I/O throughput, automatic OpenAPI documentation, dependency injection system. |
| **Relational Database** | MySQL 8.x | ACID compliance, robust InnoDB row-level locking (`SELECT ... FOR UPDATE`), widely supported across enterprise clouds. |
| **Database Driver** | PyMySQL + Cryptography | Pure Python DBAPI driver supporting MySQL 8 `caching_sha2_password` authentication without native C compilation headaches. |
| **ORM & Migrations** | SQLAlchemy 2.x & Alembic | Modern `Mapped[]` type safety, robust connection pooling with `pool_pre_ping`, declarative migration autogeneration. |
| **Task Queue** | Celery + Redis | Battle-tested asynchronous worker model, fair task prefetching, decoupling long-running I/O from client request loops. |
| **Dependency Manager** | Poetry 2.x | Deterministic lockfiles, reproducible virtual environments, clear separation of runtime vs dev/test dependencies. |
| **Code Quality** | Ruff & Pytest | Lightning-fast linting/formatting (`ruff`), isolated unit and integration test runners (`pytest`). |
| **Containers & Proxy** | Docker & Nginx | Reproducible multi-container stack, reverse proxy header normalization, liveness routing. |

---

## 4. Initial Feature Scope

The first vertical slice planned for the system is:
**Order Creation + Transactional Inventory Reservation**

- **Workflow:** Validate customer payload -> acquire row-level lock on inventory items -> verify stock availability -> deduct unreserved quantity -> persist order -> commit transaction -> enqueue asynchronous fulfillment task.
- **Scaffold Boundary:** The repository currently scaffolds the structural models, request/response schemas, API routers, and explicit service interfaces. The core business logic, transaction handling, concurrency protection, and feature tests are reserved for the responsible backend engineer.

---

## 5. Prerequisites & Local Setup

### 5.1 Prerequisites
- **Python**: `>= 3.11, < 3.13` (Tested on Python 3.11.15)
- **Poetry**: `>= 2.0.0`
- **Docker & Docker Compose**: (Optional for containerized run)
- **MySQL 8.x & Redis**: (For running native local services)

### 5.2 Local Environment Installation

1. **Clone the repository:**
   ```bash
   git clone <repo-url> ecommerce-logistics-engine
   cd ecommerce-logistics-engine
   ```

2. **Configure environment variables:**
   ```bash
   cp .env.example .env
   ```
   *Review `.env` and verify database and Redis connection credentials.*

3. **Install dependencies via Poetry:**
   ```bash
   poetry install
   ```

4. **Verify installation & activate shell:**
   ```bash
   poetry run python -c "import fastapi, sqlalchemy, celery, pymysql; print('Ready')"
   ```

---

## 6. Database Migrations (Alembic)

Database schema revisions are managed using Alembic and synchronized with SQLAlchemy models:

- **Generate a new migration:**
  ```bash
  poetry run alembic revision --autogenerate -m "create_orders_and_inventory_tables"
  ```
- **Apply pending migrations:**
  ```bash
  poetry run alembic upgrade head
  ```
- **Roll back last migration:**
  ```bash
  poetry run alembic downgrade -1
  ```
- **View current migration version:**
  ```bash
  poetry run alembic current
  ```

---

## 7. Running the Application Locally

### 7.1 Running FastAPI Server (Native)
```bash
poetry run uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```
- Interactive API Docs (Swagger): [http://localhost:8000/docs](http://localhost:8000/docs)
- Alternative Docs (ReDoc): [http://localhost:8000/redoc](http://localhost:8000/redoc)
- Health Check (Liveness): [http://localhost:8000/health](http://localhost:8000/health)
- Readiness Probe: [http://localhost:8000/ready](http://localhost:8000/ready)

### 7.2 Running Celery Worker (Native)
```bash
poetry run celery -A app.workers.celery_app.celery_app worker --loglevel=info
```

---

## 8. Docker Compose Infrastructure

The complete local environment (MySQL 8.4, Redis 7, FastAPI API, Celery Worker, Nginx Reverse Proxy) is defined in `compose.yaml`:

```bash
# Validate Compose configuration syntax
docker compose config

# Start all infrastructure services in background
docker compose up -d

# Check service health and logs
docker compose ps
docker compose logs -f api

# Stop all services
docker compose down
```

### Service Map & Exposed Ports

| Service | Container Name | Port Mapping | Health Check |
| :--- | :--- | :--- | :--- |
| **Nginx** | `logistics_nginx` | `127.0.0.1:8080:80` | `curl http://localhost/nginx-health` |
| **API** | `logistics_api` | `127.0.0.1:8000:8000` | `curl http://localhost:8000/health` |
| **Worker** | `logistics_celery_worker` | Internal network | Supervised process |
| **MySQL** | `logistics_mysql` | `127.0.0.1:3306:3306` | `mysqladmin ping` |
| **Redis** | `logistics_redis` | `127.0.0.1:6379:6379` | `redis-cli ping` |

---

## 9. Testing & Code Quality Gates

### 9.1 Test Execution
The test suite is partitioned into unit tests and integration tests via Pytest markers:

```bash
# Run all tests
poetry run pytest

# Run isolated unit tests only
poetry run pytest -m unit

# Run integration tests only
poetry run pytest -m integration
```

### 9.2 Linting & Formatting
```bash
# Check code style with Ruff
poetry run ruff check .

# Check code formatting with Ruff
poetry run ruff format --check .

# Auto-format and fix
poetry run ruff check --fix . && poetry run ruff format .
```

### 9.3 Continuous Integration (GitHub Actions)
The repository includes `.github/workflows/ci.yml` which triggers on every pull request and push to `main`:
1. Checks out repository with least-privilege token permissions (`contents: read`).
2. Configures Python 3.11 and caches Poetry virtualenv dependencies.
3. Installs locked dependencies strictly from `poetry.lock`.
4. Executes `ruff check` and `ruff format --check`.
5. Executes the unit and scaffold integration test suites.

---

## 10. Current Implementation Status & Known Limitations

### Implemented
- [x] Vertical Slice Architecture (VSA) modular structure (`orders`, `inventory`, `core`, `workers`).
- [x] Complete SQLAlchemy 2.0 domain models (`Order`, `OrderItem`, `InventoryItem`, `StockAllocation`).
- [x] Strict Pydantic v2 validation DTOs with decimal precision and boundary constraints.
- [x] FastAPI application entrypoint with lifespan events, CORS, OpenAPI schema, and health probes.
- [x] Service boundaries and runtime-checkable Protocol interfaces (`OrderServiceInterface`, `InventoryServiceInterface`).
- [x] Celery 5.x application configuration and async task stubs wired to Redis.
- [x] Alembic migration harness configured with dynamic database settings and autogenerate metadata.
- [x] Multi-stage `Dockerfile` and validated `compose.yaml` with Nginx reverse proxy.
- [x] GitHub Actions CI workflow with caching, linting, and test execution.
- [x] 14 passing unit and integration tests verifying configurations, schemas, and endpoint contracts.

### Scaffolded / Next Steps for Engineer
- [ ] Core business logic implementation in `OrderService.create_order_with_reservation()`.
- [ ] Concurrency-safe atomic inventory reservation in `InventoryService.reserve_stock_atomic()` (e.g. `SELECT ... FOR UPDATE` with sorted SKU deadlock prevention).
- [ ] Rollback handling and custom domain exceptions (e.g. `InsufficientInventoryError`).
- [ ] End-to-end transactional feature tests with a live test MySQL database.
- [ ] AWS deployment architecture implementation (ECS Fargate / Aurora MySQL / ElastiCache).
