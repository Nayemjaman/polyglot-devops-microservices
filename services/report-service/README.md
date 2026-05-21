# Report Service

FastAPI service for report snapshots, dashboard cache snapshots, export jobs, and generated report files.

## Local Setup

```bash
make setup
make migrate
make run
```

Default local address:

```text
http://127.0.0.1:8003
```

Default local database URL:

```text
postgresql+asyncpg://report_service_user:report_service_password@127.0.0.1:6434/report_service_db?prepared_statement_cache_size=0
```

## Endpoints

```text
GET /health
GET /health/db
GET /hello
GET /api/reports/monthly
GET /api/reports/yearly
GET /api/reports/income-vs-expense
GET /api/reports/category-wise
GET /api/reports/wallet-wise
GET /api/reports/budget-performance
GET /api/reports/savings
GET /api/reports/dashboard
GET /api/reports/dashboard/monthly-summary
POST /api/reports/export
GET /api/reports/export-jobs
GET /api/reports/export-jobs/{id}
GET /api/reports/files/{id}/download
```

## Tables

```text
report_snapshots
report_export_jobs
report_files
dashboard_cache_snapshots
```
