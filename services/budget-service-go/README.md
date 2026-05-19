# Budget Service

Go service built with Gin.

## Local Run

```bash
go mod tidy
go run ./cmd/api
```

Default address:

```text
:8081
```

## Endpoints

```text
GET /health
GET /hello
```

Example response:

```json
{
  "message": "hello world",
  "service": "budget-service"
}
```
