# Local service stack

This compose stack runs the frontend and backend services behind a local Caddy gateway, plus one isolated PostgreSQL database and one PgBouncer pooler for each backend service.

## Start

```bash
cd infra
cp .env.example .env
docker compose up -d
```

## EC2 deployment with DockerHub images

For a single EC2 deployment, keep `docker-compose.yml` as the base stack and add
`docker-compose.ec2.yml` as the production override. The override replaces local
`build:` contexts with DockerHub images for the application containers.

First, push all application images from GitHub Actions:

1. Open the `Polyglot Microservices CI/CD` workflow in GitHub Actions.
2. Click `Run workflow`.
3. Enable `build_all`.
4. Run it from `prod`.

This pushes all application images into one DockerHub repository with
service-prefixed tags:

- `DOCKERHUB_USER_NAME/polyglot-devops-microservices:frontend-prod`
- `DOCKERHUB_USER_NAME/polyglot-devops-microservices:auth-service-prod`
- `DOCKERHUB_USER_NAME/polyglot-devops-microservices:transaction-service-prod`
- `DOCKERHUB_USER_NAME/polyglot-devops-microservices:budget-service-prod`
- `DOCKERHUB_USER_NAME/polyglot-devops-microservices:report-service-prod`

Each image also gets a Git SHA tag, for example
`DOCKERHUB_USER_NAME/polyglot-devops-microservices:frontend-<git-sha>`.

Then on EC2:

```bash
cd infra
cp .env.ec2.example .env
# edit .env with real passwords, secrets, DockerHub username, and EC2 domain/IP
docker compose -f docker-compose.yml -f docker-compose.ec2.yml pull
docker compose -f docker-compose.yml -f docker-compose.ec2.yml up -d --no-build
```

For later deployments after CI pushes a changed image:

GitHub Actions deploys automatically after a push to the `prod` branch and a
successful `docker-build-push` job. The
`production` environment approval gate must be approved first. The deploy job:

- SSHs into EC2
- detects which service images changed from the pushed file paths
- pulls the updated image tag for only those services
- runs the matching migration service when needed
- starts the updated runtime containers as the inactive blue/green color
- waits for candidate container health checks
- recreates Caddy so traffic switches to the new color-specific upstreams
- restores the previous image tag/upstream metadata and stops candidate
  containers if health fails before the traffic switch

The workflow blocks `prod` pushes unless the pushed commit already exists in
`staging`. Promote by fast-forwarding or pushing a known-good staging commit to
`prod`; do not commit directly on `prod`.

Changed-service detection is path based:

| Changed path | Built/deployed image |
| --- | --- |
| `frontend/**` | `frontend` |
| `services/auth-service/**` | `auth-service` |
| `services/transaction-service/**` | `transaction-service` |
| `services/budget-service/**` | `budget-service` |
| `services/report-service/**` | `report-service` |
| `proto/budget/**` | `budget-service` |
| `proto/transaction/**` | `transaction-service`, `budget-service` |
| `infra/**`, `.github/workflows/ci-cd.yml` | all services |

## Blue-green Compose deployment

Production deploys use `docker-compose.blue-green.yml` in addition to the base
and EC2 override files. Shared infrastructure containers keep their stable names
and volumes. Application containers run with color-specific names such as
`transaction-service-green` or `frontend-blue`, then Caddy routes public traffic
to the active upstream stored in `.env`.

The first deployment from an existing single-color EC2 stack starts green
candidate containers and switches Caddy from the original stable service names
to the green names after health checks pass. Later deployments alternate each
changed service between `blue` and `green` independently.

The active service state is tracked in `.env`:

```env
FRONTEND_ACTIVE_COLOR=green
FRONTEND_UPSTREAM=frontend-green
TRANSACTION_SERVICE_ACTIVE_COLOR=blue
TRANSACTION_SERVICE_UPSTREAM=transaction-service-blue
```

Only changed services move to a new color. Unchanged services keep their current
upstream, so a frontend-only deploy does not restart backend containers.

You can still deploy the full current `.env` image set manually from EC2:

```bash
cd infra
sh deploy-ec2.sh
```

Use `--no-build` on EC2. The override provides DockerHub image names, while the
base compose file still contains local development `build:` entries.

With one EC2 instance and one container per service, deploys are minimal-downtime,
not true zero-downtime. True zero-downtime requires at least two replicas behind
a load balancer or a blue-green setup.

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
