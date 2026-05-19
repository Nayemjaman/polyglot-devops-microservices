# Local database stack

This compose stack runs one isolated PostgreSQL database and one PgBouncer pooler for each backend service.

## Start

```bash
cd infra
cp .env.example .env
docker compose up -d
```

## Service connection targets

Applications running inside the compose network should connect through PgBouncer:

| Service | Host | Port | Database |
| --- | --- | --- | --- |
| Auth | `auth-pgbouncer` | `6432` | `auth_service_db` |
| Budget | `budget-pgbouncer` | `6432` | `budget_service_db` |
| Report | `report-pgbouncer` | `6432` | `report_service_db` |
| Transaction | `transaction-pgbouncer` | `6432` | `transaction_service_db` |

From the host machine, use ports `6432`, `6433`, `6434`, and `6435` respectively.

## Notes

- Each service has its own database, user, volume, and PgBouncer instance.
- Application traffic should go to PgBouncer, not directly to PostgreSQL.
- PgBouncer uses transaction pooling, which is the usual default for web APIs.
- PgBouncer config is generated from compose environment variables, so database names, users, and passwords stay in one place.
- `.env` is for local development only and should not be committed. For production, use Docker secrets, Kubernetes secrets, or a deployment-specific secret manager.
- Plain PgBouncer auth is acceptable for this local Docker network baseline. For production, enable TLS and use a secret-managed PgBouncer userlist or SCRAM-compatible deployment flow.
