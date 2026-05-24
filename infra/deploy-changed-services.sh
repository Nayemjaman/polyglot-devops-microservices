#!/usr/bin/env sh
set -eu

MATRIX_FILE="${1:?usage: deploy-changed-services.sh /path/to/matrix.json}"
IMAGE_SHA="${IMAGE_SHA:?IMAGE_SHA is required}"

cd "$(dirname "$0")"

COMPOSE_FILES="-f docker-compose.yml -f docker-compose.ec2.yml"
ENV_FILE=".env"
ROLLBACK_FILE=".deploy-rollback.env"

if [ ! -f "$ENV_FILE" ]; then
  echo "$ENV_FILE is missing. Create it from .env.ec2.example first."
  exit 1
fi

set_env_value() {
  key="$1"
  value="$2"
  if grep -q "^${key}=" "$ENV_FILE"; then
    sed -i.bak "s|^${key}=.*|${key}=${value}|" "$ENV_FILE"
  else
    printf '%s=%s\n' "$key" "$value" >> "$ENV_FILE"
  fi
  rm -f "${ENV_FILE}.bak"
}

get_env_value() {
  key="$1"
  grep "^${key}=" "$ENV_FILE" | tail -n 1 | cut -d= -f2- || true
}

wait_for_health() {
  container="$1"
  attempts="${2:-30}"
  delay_seconds="${3:-5}"

  i=1
  while [ "$i" -le "$attempts" ]; do
    status="$(docker inspect --format '{{if .State.Health}}{{.State.Health.Status}}{{else}}{{.State.Status}}{{end}}' "$container" 2>/dev/null || true)"
    if [ "$status" = "healthy" ] || [ "$status" = "running" ]; then
      echo "$container is $status"
      return 0
    fi
    echo "Waiting for $container health, current status: ${status:-missing}"
    sleep "$delay_seconds"
    i=$((i + 1))
  done

  echo "$container did not become healthy"
  return 1
}

run_migration() {
  service="$1"
  case "$service" in
    auth-service)
      docker compose $COMPOSE_FILES run --rm auth-migrate
      ;;
    budget-service)
      docker compose $COMPOSE_FILES run --rm budget-migrate
      ;;
    report-service)
      docker compose $COMPOSE_FILES run --rm report-migrate
      ;;
    transaction-service)
      docker compose $COMPOSE_FILES run --rm transaction-migrate
      ;;
    frontend)
      ;;
  esac
}

runtime_services() {
  service="$1"
  case "$service" in
    frontend)
      printf '%s\n' frontend
      ;;
    auth-service)
      printf '%s\n' auth-service
      ;;
    budget-service)
      printf '%s\n' budget-service
      ;;
    report-service)
      printf '%s\n' report-service report-worker
      ;;
    transaction-service)
      printf '%s\n' transaction-service transaction-outbox-publisher
      ;;
    *)
      echo "Unknown service: $service" >&2
      return 1
      ;;
  esac
}

container_for_health() {
  service="$1"
  case "$service" in
    frontend) echo frontend ;;
    auth-service) echo auth-service ;;
    budget-service) echo budget-service ;;
    report-service) echo report-service ;;
    transaction-service) echo transaction-service ;;
  esac
}

tag_key_for_service() {
  service="$1"
  case "$service" in
    frontend) echo FRONTEND_IMAGE_TAG ;;
    auth-service) echo AUTH_SERVICE_IMAGE_TAG ;;
    budget-service) echo BUDGET_SERVICE_IMAGE_TAG ;;
    report-service) echo REPORT_SERVICE_IMAGE_TAG ;;
    transaction-service) echo TRANSACTION_SERVICE_IMAGE_TAG ;;
    *)
      echo "Unknown service: $service" >&2
      return 1
      ;;
  esac
}

rollback_service() {
  service="$1"
  key="$(tag_key_for_service "$service")"
  previous_tag="$(grep "^${key}=" "$ROLLBACK_FILE" | tail -n 1 | cut -d= -f2- || true)"

  if [ -z "$previous_tag" ]; then
    echo "No previous tag found for $service; cannot roll back automatically."
    return 1
  fi

  echo "Rolling back $service to $previous_tag"
  set_env_value "$key" "$previous_tag"
  docker compose $COMPOSE_FILES pull $(runtime_services "$service")
  docker compose $COMPOSE_FILES up -d --no-build $(runtime_services "$service")
  wait_for_health "$(container_for_health "$service")"
}

deploy_service() {
  service="$1"
  key="$(tag_key_for_service "$service")"
  previous_tag="$(get_env_value "$key")"
  new_tag="${service}-${IMAGE_SHA}"

  echo "${key}=${previous_tag}" >> "$ROLLBACK_FILE"
  echo "Deploying $service with tag $new_tag"
  set_env_value "$key" "$new_tag"

  if ! docker compose $COMPOSE_FILES pull $(runtime_services "$service"); then
    rollback_service "$service"
    return 1
  fi

  if ! run_migration "$service"; then
    rollback_service "$service"
    return 1
  fi

  if ! docker compose $COMPOSE_FILES up -d --no-build --no-deps $(runtime_services "$service"); then
    rollback_service "$service"
    return 1
  fi

  if ! wait_for_health "$(container_for_health "$service")"; then
    rollback_service "$service"
    return 1
  fi
}

rm -f "$ROLLBACK_FILE"
touch "$ROLLBACK_FILE"

services="$(grep -o '"name":"[^"]*"' "$MATRIX_FILE" | cut -d\" -f4)"
if [ -z "$services" ]; then
  echo "No services found in $MATRIX_FILE"
  exit 0
fi

failed=0
for service in $services; do
  if ! deploy_service "$service"; then
    failed=1
  fi
done

docker compose $COMPOSE_FILES ps
exit "$failed"
