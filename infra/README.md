# Local service stack

This compose stack runs the frontend and backend services behind a local Caddy gateway, plus one isolated PostgreSQL database and one PgBouncer pooler for each backend service.

## Start

```bash
cd infra
cp .env.example .env
docker compose up -d
```

## Public entrypoints

Use the gateway instead of calling services directly:

| Protocol | URL |
| --- | --- |
| HTTP | `http://127.0.0.1:8080` |
| HTTPS with Caddy internal CA | `https://127.0.0.1:8443` |

The frontend is served from the gateway root. API routes stay on the same origin and are forwarded by Caddy to the backend services.

For local HTTPS testing with curl, use `-k` unless you install Caddy's local CA certificate.

## API smoke test

The root `api_smoke_test.py` script calls each service on a direct localhost port. Start the stack with the smoke-test port override when you want to run it from the host:

```bash
cd infra
docker compose -f docker-compose.yml -f docker-compose.smoke-ports.yml up -d
cd ..
python3 api_smoke_test.py --email smoke@example.com --password 'StrongPass123!'
```

## Gateway routes

| Path | Upstream |
| --- | --- |
| `/auth/*` | `auth-service:8000` |
| `/api/budgets*` | `budget-service:8001` |
| `/api/reports*` | `report-service:8003` |
| `/api/*` | `transaction-service:8002` |
| `/*` | `frontend:3000` |

## Service connection targets

Applications running inside the compose network should connect through PgBouncer:

| Service | Host | Port | Database |
| --- | --- | --- | --- |
| Auth | `auth-pgbouncer` | `6432` | `auth_service_db` |
| Budget | `budget-pgbouncer` | `6432` | `budget_service_db` |
| Report | `report-pgbouncer` | `6432` | `report_service_db` |
| Transaction | `transaction-pgbouncer` | `6432` | `transaction_service_db` |

Database and service ports are intentionally private to the compose network. Use the gateway for application traffic. If you need host DB access during development, add a local-only compose override instead of publishing DB ports in the shared compose file.

## Notes

- Each service has its own database, user, volume, and PgBouncer instance.
- Application traffic should go to PgBouncer, not directly to PostgreSQL.
- PgBouncer uses transaction pooling, which is the usual default for web APIs.
- Compose now requires passwords and service secrets from `.env`; default production-like passwords are not embedded in the shared compose file.
- `.env` is for local development only and should not be committed. For production, use Docker secrets, Kubernetes secrets, AWS Secrets Manager, SSM Parameter Store, or another deployment-specific secret manager.
- Plain PgBouncer auth is acceptable for this local Docker network baseline. For production, enable TLS and use a secret-managed PgBouncer userlist or SCRAM-compatible deployment flow.
- Caddy's `tls internal` is suitable for local HTTPS. For public production HTTPS, configure a real domain and ACME issuer or provide certificates from your platform load balancer.
