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
```

Example response:

```json
{
  "message": "hello FirstName LastName",
  "service": "budget-service"
}
```
