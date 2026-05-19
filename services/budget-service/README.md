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
