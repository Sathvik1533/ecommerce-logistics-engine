# System Architecture — E-Commerce Logistics Engine

## 1. Architectural Philosophy: Vertical Slice Architecture (VSA)

Traditional layered architectures organize code horizontally (`controllers/`, `services/`, `repositories/`, `models/`). In complex domains like logistics and fulfillment, this often leads to:
- High coupling across layers for single features.
- Fragmented business rules scattered across multiple arbitrary directories.
- Unclear ownership of transactional invariants.

The **E-Commerce Logistics Engine** adopts **Vertical Slice Architecture (VSA)** organized as a **Modular Monolith**:
- Code is structured around **business capabilities** (`app/features/orders`, `app/features/inventory`).
- Each feature slice contains its domain models, schemas, routers, and internal services.
- Cross-slice interactions occur through explicit service boundaries / interfaces rather than direct internal state mutations.
- Technical cross-cutting concerns (connection pooling, configuration, telemetry) reside in `app/core/`.
- Asynchronous and event-driven background processing resides in `app/workers/`.

---

## 2. Feature Boundaries & Core Responsibilities

```
app/
├── core/                   # Shared Infrastructure
│   ├── config.py           # Typed settings & environment parsing
│   └── database.py         # SQLAlchemy 2.0 engine, pool & session management
├── features/               # Business Capabilities (Vertical Slices)
│   ├── orders/             # Order lifecycle, line items, state transitions
│   │   ├── models.py       # Order, OrderItem, OrderStatus
│   │   ├── schemas.py      # Request / Response DTOs
│   │   ├── service.py      # Order orchestrator & transactional boundaries
│   │   └── router.py       # REST API endpoints (/api/v1/orders)
│   └── inventory/          # Stock allocation, reservations, warehouse logic
│       ├── models.py       # InventoryItem, StockAllocation, AllocationStatus
│       ├── schemas.py      # Reservation requests & stock checks
│       ├── service.py      # Concurrency-safe inventory reservations
│       └── router.py       # Inventory endpoints (/api/v1/inventory)
└── workers/                # Asynchronous Workers
    ├── celery_app.py       # Celery application & Redis broker wiring
    └── tasks.py            # Follow-up asynchronous event tasks
```

---

## 3. Order Creation & Transactional Inventory Reservation Flow

The core workflow ensures that an order is only confirmed when all required inventory is atomically secured without overselling or race conditions.

```
Client (Web/App)
       │
       ▼  POST /api/v1/orders/
  [OrderRouter]
       │
       ▼  create_order_with_reservation()
  [OrderService]
       │
       ├────────────────── BEGIN TRANSACTION ──────────────────┐
       │                                                       │
       │  1. reserve_stock_atomic(order_ref, items)            │
       ▼                                                       │
  [InventoryService]                                           │
       │                                                       │
       │  2. SELECT * FROM inventory_items                     │
       │     WHERE sku IN (...)                                │
       │     ORDER BY sku ASC                                  │
       │     FOR UPDATE;  <── [Row-Level Lock Acquired]        │
       │                                                       │
       │  3. Verify available_qty >= requested_qty             │
       │     If insufficient: RAISE InsufficientStock ─────────┼──> ROLLBACK
       │                                                       │
       │  4. Increment reserved_quantity                       │
       │     Insert StockAllocation(status=RESERVED)           │
       │                                                       │
       ▼  5. Stock Reserved Successfully                       │
  [OrderService]                                               │
       │                                                       │
       │  6. Insert Order(status=CONFIRMED) & OrderItems       │
       │                                                       │
       ├────────────────── COMMIT TRANSACTION ─────────────────┘
       │
       │  7. Dispatched only AFTER successful commit
       ▼
  [Celery Task: send_order_confirmation_task.delay(order_ref)]
       │
       ▼
  Return HTTP 201 Created (OrderResponse)
```

---

## 4. Concurrency Protection & Transaction Boundaries

### 4.1 The Race Condition Threat
In high-throughput e-commerce events (e.g., flash sales, holiday drops), hundreds of concurrent requests attempt to reserve the same finite inventory simultaneously. Without concurrency controls:
- Two sessions check stock `available = 1` concurrently.
- Both proceed to reserve.
- Stock becomes `-1` (overselling).

### 4.2 Concurrency Strategies

| Strategy | Mechanism | Pros | Cons / Trade-offs |
| :--- | :--- | :--- | :--- |
| **Pessimistic Locking (`SELECT ... FOR UPDATE`)** *(Recommended for Initial Stage)* | Locks the target inventory rows in MySQL inside the transaction until commit/rollback. | Complete consistency; prevents race conditions at the database engine level; straightforward to reason about. | Holds locks for the duration of the transaction; requires dead-lock mitigation via sorted SKU acquisition. |
| **Optimistic Locking (`version` column)** | Checks `WHERE id = :id AND version = :version` on UPDATE. | Non-blocking reads; performant when conflicts are rare. | High retry rate and latency under intense hot-spot contention. |
| **Distributed Redis Locks (Redlock)** | Coordinates locks in memory prior to hitting the database. | Relieves database lock manager under massive scale. | Introduces split-brain risks, lease expiration races, and dual-system complexity. |

### 4.3 Deadlock Mitigation via Predictable SKU Ordering
When multiple concurrent transactions lock multiple items (e.g., Order A locks SKU-1 then SKU-2; Order B locks SKU-2 then SKU-1), a database deadlock occurs.
**Rule:** The reservation service must sort requested SKUs alphabetically (`ORDER BY sku ASC`) before acquiring row locks, ensuring a uniform lock hierarchy across all transactions.

### 4.4 Transaction Boundaries & Asynchronous Tasks
Background tasks (Celery) **must never be enqueued prior to transaction commit**. If enqueued before commit:
- The worker may execute before MySQL commits the transaction, causing a "record not found" error (ghost read).
- If the transaction subsequently rolls back, the worker has already sent out an illegitimate confirmation email.

---

## 5. Future AWS Deployment Target

When transitioning from the local environment to AWS:

```
[ Route 53 / AWS CloudFront ]
              │
              ▼
    [ Application Load Balancer (ALB) ]
              │
      ┌───────┴───────┐
      ▼               ▼
[ ECS Fargate: API ] [ ECS Fargate: Celery Worker ]
      │               │
      ├───────────────┼───────────────┐
      ▼                               ▼
[ Amazon Aurora MySQL ]     [ Amazon ElastiCache Redis ]
  (Multi-AZ Cluster)          (Redis Cluster Mode)
```

1. **API & Workers:** Containerized deployment on **AWS ECS Fargate** or **EKS** with auto-scaling based on CPU/Memory and SQS/Redis queue depth.
2. **Database:** **Amazon Aurora MySQL** (Multi-AZ with automatic failover and read replicas for analytics/reporting).
3. **Cache & Broker:** **Amazon ElastiCache for Redis** with multi-AZ replication.
4. **Ingress & Proxy:** Local Nginx is superseded by **AWS Application Load Balancer (ALB)** and **CloudFront** (handling TLS termination, WAF rate limiting, and DDoS mitigation).
5. **Configuration & Secrets:** **AWS Secrets Manager** and **SSM Parameter Store** for zero-trust credential distribution.
