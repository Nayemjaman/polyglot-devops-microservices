#!/usr/bin/env sh
set -eu

MATRIX_FILE="${1:?usage: deploy-changed-services.sh /path/to/matrix.json}"
IMAGE_SHA="${IMAGE_SHA:?IMAGE_SHA is required}"

cd "$(dirname "$0")"

COMPOSE_FILES="-f docker-compose.yml -f docker-compose.ec2.yml"
BLUE_GREEN_COMPOSE_FILES="$COMPOSE_FILES -f docker-compose.blue-green.yml"
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
  default="${2:-}"
  value="$(grep "^${key}=" "$ENV_FILE" | tail -n 1 | cut -d= -f2- || true)"
  if [ -n "$value" ]; then
    printf '%s\n' "$value"
  else
    printf '%s\n' "$default"
  fi
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

active_color_key_for_service() {
  service="$1"
  case "$service" in
    frontend) echo FRONTEND_ACTIVE_COLOR ;;
    auth-service) echo AUTH_SERVICE_ACTIVE_COLOR ;;
    budget-service) echo BUDGET_SERVICE_ACTIVE_COLOR ;;
    report-service) echo REPORT_SERVICE_ACTIVE_COLOR ;;
    transaction-service) echo TRANSACTION_SERVICE_ACTIVE_COLOR ;;
    *)
      echo "Unknown service: $service" >&2
      return 1
      ;;
  esac
}

upstream_key_for_service() {
  service="$1"
  case "$service" in
    frontend) echo FRONTEND_UPSTREAM ;;
    auth-service) echo AUTH_SERVICE_UPSTREAM ;;
    budget-service) echo BUDGET_SERVICE_UPSTREAM ;;
    report-service) echo REPORT_SERVICE_UPSTREAM ;;
    transaction-service) echo TRANSACTION_SERVICE_UPSTREAM ;;
    *)
      echo "Unknown service: $service" >&2
      return 1
      ;;
  esac
}

opposite_color() {
  color="$1"
  if [ "$color" = "green" ]; then
    echo blue
  else
    echo green
  fi
}

container_for_service_color() {
  service="$1"
  color="$2"
  echo "${service}-${color}"
}

colored_runtime_services() {
  service="$1"
  color="$2"
  case "$service" in
    frontend)
      printf '%s\n' "frontend-${color}"
      ;;
    auth-service)
      printf '%s\n' "auth-service-${color}"
      ;;
    budget-service)
      printf '%s\n' "budget-service-${color}"
      ;;
    report-service)
      printf '%s\n' "report-service-${color}" "report-worker-${color}"
      ;;
    transaction-service)
      printf '%s\n' "transaction-service-${color}" "transaction-outbox-publisher-${color}"
      ;;
    *)
      echo "Unknown service: $service" >&2
      return 1
      ;;
  esac
}

save_rollback_value() {
  service="$1"
  key="$2"
  value="$3"
  printf '%s__%s=%s\n' "$service" "$key" "$value" >> "$ROLLBACK_FILE"
}

get_rollback_value() {
  service="$1"
  key="$2"
  grep "^${service}__${key}=" "$ROLLBACK_FILE" | tail -n 1 | cut -d= -f2- || true
}

prepare_service() {
  service="$1"
  tag_key="$(tag_key_for_service "$service")"
  color_key="$(active_color_key_for_service "$service")"
  upstream_key="$(upstream_key_for_service "$service")"

  previous_tag="$(get_env_value "$tag_key")"
  previous_color="$(get_env_value "$color_key" blue)"
  previous_upstream="$(get_env_value "$upstream_key" "$service")"
  candidate_color="$(opposite_color "$previous_color")"
  candidate_upstream="$(container_for_service_color "$service" "$candidate_color")"
  new_tag="${service}-${IMAGE_SHA}"

  save_rollback_value "$service" "$tag_key" "$previous_tag"
  save_rollback_value "$service" "$color_key" "$previous_color"
  save_rollback_value "$service" "$upstream_key" "$previous_upstream"
  save_rollback_value "$service" CANDIDATE_COLOR "$candidate_color"

  echo "Preparing $service as $candidate_color with tag $new_tag"
  set_env_value "$tag_key" "$new_tag"
  set_env_value "$color_key" "$candidate_color"
  set_env_value "$upstream_key" "$candidate_upstream"
}

pull_candidate() {
  service="$1"
  candidate_color="$(get_rollback_value "$service" CANDIDATE_COLOR)"
  docker compose $BLUE_GREEN_COMPOSE_FILES pull $(colored_runtime_services "$service" "$candidate_color")
}

start_candidate() {
  service="$1"
  candidate_color="$(get_rollback_value "$service" CANDIDATE_COLOR)"
  docker compose $BLUE_GREEN_COMPOSE_FILES up -d --no-build --no-deps $(colored_runtime_services "$service" "$candidate_color")
}

stop_service_color() {
  service="$1"
  color="$2"
  docker compose $BLUE_GREEN_COMPOSE_FILES stop $(colored_runtime_services "$service" "$color") >/dev/null 2>&1 || true
}

restore_service_env() {
  service="$1"
  tag_key="$(tag_key_for_service "$service")"
  color_key="$(active_color_key_for_service "$service")"
  upstream_key="$(upstream_key_for_service "$service")"

  set_env_value "$tag_key" "$(get_rollback_value "$service" "$tag_key")"
  set_env_value "$color_key" "$(get_rollback_value "$service" "$color_key")"
  set_env_value "$upstream_key" "$(get_rollback_value "$service" "$upstream_key")"
}

rollback_all() {
  echo "Rolling back deployment metadata and stopping candidate containers"
  for service in $services; do
    candidate_color="$(get_rollback_value "$service" CANDIDATE_COLOR)"
    [ -n "$candidate_color" ] && stop_service_color "$service" "$candidate_color"
    restore_service_env "$service"
  done
  docker compose $BLUE_GREEN_COMPOSE_FILES up -d --no-build --no-deps gateway || true
}

switch_gateway() {
  echo "Switching gateway to the new upstreams"
  docker compose $BLUE_GREEN_COMPOSE_FILES up -d --no-build --no-deps gateway
  wait_for_health gateway 12 5
}

cleanup_previous_colors() {
  for service in $services; do
    previous_color="$(get_rollback_value "$service" "$(active_color_key_for_service "$service")")"
    previous_upstream="$(get_rollback_value "$service" "$(upstream_key_for_service "$service")")"
    if [ "$previous_upstream" = "$(container_for_service_color "$service" "$previous_color")" ]; then
      echo "Stopping previous $service $previous_color containers"
      stop_service_color "$service" "$previous_color"
    fi
  done
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
  prepare_service "$service"
done

for service in $services; do
  if ! pull_candidate "$service"; then
    failed=1
  fi
done

if [ "$failed" -eq 0 ]; then
  for service in $services; do
    if ! run_migration "$service"; then
      failed=1
    fi
  done
fi

if [ "$failed" -eq 0 ]; then
  for service in $services; do
    if ! start_candidate "$service"; then
      failed=1
    fi
  done
fi

if [ "$failed" -eq 0 ]; then
  for service in $services; do
    candidate_color="$(get_rollback_value "$service" CANDIDATE_COLOR)"
    if ! wait_for_health "$(container_for_service_color "$service" "$candidate_color")"; then
      failed=1
    fi
  done
fi

if [ "$failed" -eq 0 ]; then
  if ! switch_gateway; then
    failed=1
  fi
fi

if [ "$failed" -ne 0 ]; then
  rollback_all
  docker compose $BLUE_GREEN_COMPOSE_FILES ps
  exit 1
fi

cleanup_previous_colors
docker compose $BLUE_GREEN_COMPOSE_FILES ps
