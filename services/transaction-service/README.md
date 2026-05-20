# Transaction Service

Async FastAPI service for transaction APIs.

## Structure

```text
app/api/routes/       HTTP route handlers grouped by resource
app/api/presenters.py ORM-to-response mapping helpers
app/clients/          outbound service clients
app/core/             configuration
app/db/               SQLAlchemy base and async session setup
app/models/           SQLAlchemy table models
app/schemas/          Pydantic request/response schemas grouped by resource
app/services/         business logic grouped by resource
app/storage/          MinIO/S3 attachment storage client and object keys
```

## Local Run

```bash
make setup
make run
```

Default address:

```text
:8002
```

## Endpoints

```text
GET /health
GET /health/db
GET /health/storage
GET /hello
POST   /api/wallets
GET    /api/wallets
GET    /api/wallets/{id}
PATCH  /api/wallets/{id}
DELETE /api/wallets/{id}
POST   /api/categories
GET    /api/categories
GET    /api/categories/{id}
PATCH  /api/categories/{id}
DELETE /api/categories/{id}
POST   /api/payment-methods
GET    /api/payment-methods
PATCH  /api/payment-methods/{id}
DELETE /api/payment-methods/{id}
POST   /api/transactions
GET    /api/transactions
GET    /api/transactions/{id}
PATCH  /api/transactions/{id}
DELETE /api/transactions/{id}
GET    /api/transactions/summary/monthly
GET    /api/transactions/summary/yearly
GET    /api/transactions/summary/category-wise
GET    /api/transactions/summary/wallet-wise
POST   /api/recurring-transactions
GET    /api/recurring-transactions
PATCH  /api/recurring-transactions/{id}
DELETE /api/recurring-transactions/{id}
POST   /api/transactions/{transaction_id}/attachments
GET    /api/transactions/{transaction_id}/attachments
DELETE /api/transactions/{transaction_id}/attachments/{attachment_id}
POST   /api/tags
GET    /api/tags
DELETE /api/tags/{id}
```

`GET /hello` forwards the caller's `Authorization` header to auth service `GET /auth/me`.

Authenticated response:

```json
{
  "message": "hello FirstName LastName",
  "service": "transaction-service"
}
```

## Database

The service uses async SQLAlchemy 2.0 with PostgreSQL through `asyncpg`.

```bash
alembic upgrade head
```

Default local database URL:

```text
postgresql+asyncpg://transaction_service_user:transaction_service_password@127.0.0.1:6435/transaction_service_db
```

## Attachment Storage

Attachments are stored in an S3-compatible MinIO bucket in Docker.

Default local bucket:

```text
transaction-attachments
```

Default object key structure:

```text
attachments/{user_id}/transactions/{transaction_id}/attachments/{attachment_id}/{filename}
```

Local MinIO endpoints:

```text
S3 API:  http://127.0.0.1:9000
Console: http://127.0.0.1:9001
```
