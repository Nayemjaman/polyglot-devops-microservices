# Polyglot DevOps Microservices

A production-style personal finance platform built to demonstrate end-to-end
DevOps, backend engineering, distributed service design, observability, and a
modern frontend. The system is intentionally polyglot: each service uses a
technology that fits its responsibility while running under one Dockerized,
gateway-routed platform.

## Project Highlights

- Polyglot microservices architecture using Django REST Framework, FastAPI, Go,
  and Next.js.
- Docker Compose platform with Caddy reverse proxy, per-service PostgreSQL
  databases, PgBouncer connection pooling, Redis, RabbitMQ, and MinIO.
- GitHub Actions CI/CD pipeline with linting, tests, Docker builds, Trivy
  security scans, SonarQube support, DockerHub publishing, and EC2 deployment.
- Blue-green production deployment strategy for changed services.
- Prometheus and Grafana monitoring stack with service, gateway, database,
  queue, cache, object storage, host, and container metrics.
- Internal gRPC proto contracts for service-to-service communication between
  transaction and budget/report workflows.
- Finance domain APIs for authentication, transactions, wallets, budgets,
  reports, export jobs, file attachments, and dashboard summaries.

## DevOps

This project is designed as a DevOps-first microservices platform rather than a
single application.

### Containerization

- Each application has its own Dockerfile.
- The full stack runs through Docker Compose from the `infra` directory.
- Runtime containers use hardened defaults where practical:
  - read-only root filesystem
  - dropped Linux capabilities
  - `no-new-privileges`
  - bounded `/tmp` tmpfs
  - health checks
  - JSON log rotation

### Gateway and Routing

Caddy is used as the public gateway for both local and production-like
deployments.

| Public path | Upstream service |
| --- | --- |
| `/auth/*` | `auth-service:8000` |
| `/api/budgets*` | `budget-service:8001` |
| `/api/reports*` | `report-service:8003` |
| `/api/*` | `transaction-service:8002` |
| `/*` | `frontend:3000` |

Local gateway entrypoints:

| Protocol | URL |
| --- | --- |
| HTTP | `http://127.0.0.1:8080` |
| HTTPS with Caddy internal CA | `https://127.0.0.1:8443` |

### CI/CD Pipeline

GitHub Actions workflow: `.github/workflows/ci-cd.yml`

The pipeline includes:

- Branch policy enforcement for production deployments.
- Frontend lint and production build.
- Python linting and tests for Django/FastAPI services.
- Go formatting, vetting, and tests.
- Repository security scan with Trivy.
- Docker dry-run builds for pull requests and staging pushes.
- Docker image build and push to DockerHub on production deployment.
- Trivy image scanning after Docker builds.
- Optional SonarQube/SonarCloud code quality scan.
- EC2 deployment over SSH after production approval.

Production image tags follow this structure:

```text
DOCKERHUB_USER_NAME/polyglot-devops-microservices:<service>-<git-sha>
DOCKERHUB_USER_NAME/polyglot-devops-microservices:<service>-prod
```

### Changed-Service Deployment

The production workflow detects changed paths and only rebuilds/deploys the
affected services.

| Changed path | Affected image |
| --- | --- |
| `frontend/**` | `frontend` |
| `services/auth-service/**` | auth plus dependent backend services |
| `services/transaction-service/**` | `transaction-service` |
| `services/budget-service/**` | `budget-service` |
| `services/report-service/**` | `report-service` |
| `proto/budget/**` | `budget-service` |
| `proto/transaction/**` | `transaction-service`, `budget-service` |
| `infra/**`, `.github/workflows/ci-cd.yml` | all services |

### Blue-Green Deployment

Production deployment supports a blue-green Compose strategy:

- Shared infrastructure containers keep stable names and volumes.
- Application containers run with color-specific names such as
  `frontend-blue`, `frontend-green`, `transaction-service-blue`, and
  `transaction-service-green`.
- Caddy routes traffic to the currently active upstream.
- Changed services can move to a new color independently.
- If a candidate service fails health checks before the traffic switch, the
  deployment script restores the previous upstream metadata.

### Observability

The optional monitoring override adds:

- Prometheus
- Grafana
- Node Exporter
- cAdvisor
- PostgreSQL exporters
- PgBouncer exporters
- Redis exporter
- RabbitMQ Prometheus metrics
- MinIO metrics
- Caddy admin metrics
- Application `/metrics` endpoints

Grafana is provisioned with dashboards for:

- Platform overview
- Data layer health

## Backend

The backend is split into independent services with separate databases and
clear ownership boundaries.

### Auth Service

Location: `services/auth-service`

Stack:

- Django 5
- Django REST Framework
- Simple JWT
- PostgreSQL
- Gunicorn + Uvicorn worker

Responsibilities:

- User registration
- Login
- Token refresh
- Current-user profile
- Logout
- Auth middleware support for downstream services
- Metrics endpoint

Core routes:

```text
POST  /auth/register
POST  /auth/login
POST  /auth/refresh
GET   /auth/me
PATCH /auth/me
POST  /auth/logout
GET   /metrics
```

### Transaction Service

Location: `services/transaction-service`

Stack:

- FastAPI
- Async SQLAlchemy
- Alembic
- PostgreSQL
- MinIO/S3-compatible object storage
- RabbitMQ outbox publisher

Responsibilities:

- Wallets
- Categories
- Payment methods
- Transactions
- Recurring transactions
- Tags
- Transaction attachments
- Monthly, yearly, category-wise, and wallet-wise summaries
- Auth-service integration
- Storage health checks
- Event publishing through an outbox model

Core route groups:

```text
GET    /health
GET    /health/db
GET    /health/storage
POST   /api/wallets
GET    /api/wallets
POST   /api/categories
GET    /api/categories
POST   /api/payment-methods
GET    /api/payment-methods
POST   /api/transactions
GET    /api/transactions
PATCH  /api/transactions/{id}
DELETE /api/transactions/{id}
GET    /api/transactions/summary/monthly
GET    /api/transactions/summary/yearly
GET    /api/transactions/summary/category-wise
GET    /api/transactions/summary/wallet-wise
POST   /api/recurring-transactions
GET    /api/recurring-transactions
POST   /api/transactions/{transaction_id}/attachments
GET    /api/transactions/{transaction_id}/attachments
POST   /api/tags
GET    /api/tags
```

### Budget Service

Location: `services/budget-service`

Stack:

- Go
- Gin
- GORM
- PostgreSQL
- RabbitMQ consumer
- Internal gRPC contract structure

Responsibilities:

- Budget CRUD
- Budget categories
- Budget alert rules
- Monthly budget status
- Category-wise budget status
- Budget usage reporting
- Auth-service integration
- Transaction event consumption

Core routes:

```text
GET    /health
GET    /metrics
POST   /api/budgets
GET    /api/budgets
GET    /api/budgets/{id}
PATCH  /api/budgets/{id}
DELETE /api/budgets/{id}
POST   /api/budgets/{id}/categories
GET    /api/budgets/{id}/categories
POST   /api/budgets/{id}/alert-rules
GET    /api/budgets/{id}/alert-rules
GET    /api/budgets/status/monthly
GET    /api/budgets/status/category-wise
GET    /api/budgets/{id}/usage
```

### Report Service

Location: `services/report-service`

Stack:

- FastAPI
- Async SQLAlchemy
- Alembic
- PostgreSQL
- Redis cache
- RabbitMQ worker

Responsibilities:

- Monthly and yearly reports
- Income vs expense reports
- Category-wise and wallet-wise reports
- Budget performance reports
- Savings reports
- Dashboard summaries
- Cached dashboard snapshots
- Report export jobs
- Generated report files
- Async export worker

Core routes:

```text
GET  /health
GET  /health/db
GET  /api/reports/monthly
GET  /api/reports/yearly
GET  /api/reports/income-vs-expense
GET  /api/reports/category-wise
GET  /api/reports/wallet-wise
GET  /api/reports/budget-performance
GET  /api/reports/savings
GET  /api/reports/dashboard
POST /api/reports/export
GET  /api/reports/export-jobs
GET  /api/reports/files/{id}/download
```

## Other Architecture Components

### Data Layer

Each backend service owns its own PostgreSQL database.

| Service | Database | Pooler |
| --- | --- | --- |
| Auth | `auth_service_db` | `auth-pgbouncer` |
| Budget | `budget_service_db` | `budget-pgbouncer` |
| Report | `report_service_db` | `report-pgbouncer` |
| Transaction | `transaction_service_db` | `transaction-pgbouncer` |

PgBouncer is used between services and PostgreSQL to support connection pooling
and production-style database access.

### Messaging

RabbitMQ is used for asynchronous service communication.

- Transaction events are published for downstream consumers.
- Budget service consumes transaction-related events.
- Report service consumes transaction events and export-job requests.
- Report worker runs separately from the HTTP API container.

### Cache and Object Storage

- Redis is used by the report service for dashboard/report caching.
- MinIO provides S3-compatible storage for transaction attachments and generated
  assets.

### API Smoke Testing

The root `api_smoke_test.py` script exercises the main API flows across all
services using one user account.

Example:

```bash
cd infra
docker compose -f docker-compose.yml -f docker-compose.smoke-ports.yml up -d

cd ..
python3 api_smoke_test.py --email smoke@example.com --password 'StrongPass123!'
```

### Proto Contracts

Internal service contracts live in:

```text
proto/transaction/v1/transaction.proto
proto/budget/v1/budget.proto
```

### Internal gRPC Service Communication

The project includes proto-first internal contracts for backend-to-backend
communication. These contracts are kept outside the public HTTP API so internal
services can exchange typed finance data without exposing those calls through
the gateway.

Transaction service contract:

```text
TransactionService.GetUserMonthlySummary
TransactionService.GetUserCategorySpending
TransactionService.GetUserTransactionsForReport
```

Budget service contract:

```text
BudgetService.GetUserBudgetStatus
BudgetService.GetUserBudgetCategoryStatus
```

These contracts support workflows such as:

- Budget service reading transaction summary data for budget usage checks.
- Report service reading transaction records for generated reports.
- Backend services sharing typed request/response models through `.proto`
  definitions.
- Service-to-service calls secured separately from browser-facing HTTP routes.

## Frontend

Location: `frontend`

Stack:

- Next.js 15
- React 19
- TypeScript
- Tailwind CSS
- TanStack Query
- React Hook Form
- Zod
- Lucide React

Responsibilities:

- Authentication pages
- Protected dashboard
- Finance workspace UI
- Wallets, budgets, transactions, reports, and payment method views
- API integration with the gateway-routed backend services
- Session handling and protected-route gating

Frontend scripts:

```bash
npm run dev
npm run build
npm run start
npm run lint
```

## Run Locally

```bash
cd infra
cp .env.example .env
docker compose up -d
```

Then open:

```text
http://127.0.0.1:8080
```

For monitoring:

```bash
cd infra
docker compose -f docker-compose.yml -f docker-compose.monitoring.yml up -d
```

Monitoring URLs:

| Tool | URL |
| --- | --- |
| Prometheus | `http://127.0.0.1:9090` |
| Grafana | `http://127.0.0.1:3001` |

## Skills Demonstrated

- DevOps engineering
- Docker and Docker Compose
- CI/CD with GitHub Actions
- Blue-green deployment
- EC2 deployment automation
- DockerHub image publishing
- Trivy vulnerability scanning
- SonarQube/SonarCloud integration
- Prometheus and Grafana observability
- Reverse proxy and gateway routing with Caddy
- PostgreSQL database design
- PgBouncer connection pooling
- Redis caching
- RabbitMQ event-driven architecture
- MinIO/S3-compatible object storage
- Django REST Framework backend development
- FastAPI backend development
- Go backend development with Gin and GORM
- Async SQLAlchemy and Alembic migrations
- JWT authentication
- API smoke testing
- Next.js, React, TypeScript, and Tailwind frontend development

## Repository Structure

```text
.
|-- frontend/                    # Next.js finance dashboard
|-- infra/                       # Docker Compose, Caddy, deployment, monitoring
|-- proto/                       # Internal service contracts
|-- services/
|   |-- auth-service/            # Django REST Framework auth API
|   |-- budget-service/          # Go/Gin budget API
|   |-- report-service/          # FastAPI report API and worker
|   `-- transaction-service/     # FastAPI transaction API
|-- api_smoke_test.py            # End-to-end API smoke test script
`-- sonar-project.properties     # SonarQube project configuration
```

