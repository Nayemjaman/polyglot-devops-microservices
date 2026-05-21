# Budget Service

Go service built with Gin.

## Local Run

```bash
make tidy
make run
```

Default address:

```text
:8081
```

Default database URL:

```text
postgres://budget_service_user:budget_service_password@127.0.0.1:6433/budget_service_db?sslmode=disable
```

The service runs GORM migrations on startup for:

```text
budgets
budget_categories
budget_alert_rules
budget_history
```

## Endpoints

```text
GET /health
GET /hello
POST /api/budgets
GET /api/budgets
GET /api/budgets/{id}
PATCH /api/budgets/{id}
DELETE /api/budgets/{id}
POST /api/budgets/{id}/categories
GET /api/budgets/{id}/categories
PATCH /api/budgets/{id}/categories/{category_id}
DELETE /api/budgets/{id}/categories/{category_id}
POST /api/budgets/{id}/alert-rules
GET /api/budgets/{id}/alert-rules
PATCH /api/budgets/{id}/alert-rules/{rule_id}
DELETE /api/budgets/{id}/alert-rules/{rule_id}
GET /api/budgets/status/monthly
GET /api/budgets/status/category-wise
GET /api/budgets/{id}/usage
```

Example response:

```json
{
  "message": "hello FirstName LastName",
  "service": "budget-service"
}
```

## gRPC Contracts

Internal gRPC contracts live at:

```text
../../proto/transaction/v1/transaction.proto
../../proto/budget/v1/budget.proto
```

The HTTP status endpoints are already behind a transaction summary client interface. Generate the proto bindings before replacing the current unavailable transaction client with the real gRPC client.
