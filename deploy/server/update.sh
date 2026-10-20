#!/usr/bin/env bash
# Deploys what is on the branch the server follows: pull, rebuild, migrate, restart, check. Safe to run again.
set -euo pipefail
cd "$(dirname "$0")"

git pull --ff-only

# Shown on the Console's Server screen.
export APP_VERSION="$(git rev-parse --short HEAD)"
export DEPLOYED_AT="$(date -u +%FT%TZ)"

# The migrate service runs first; the API, worker and beat wait for it (docker-compose.yml).
docker compose up -d --build --remove-orphans
docker image prune -f >/dev/null

api_domain="$(grep -E '^API_DOMAIN=' .env | cut -d= -f2)"
for _ in $(seq 1 30); do
  if curl -fsS "https://$api_domain/api/health/"; then
    echo
    echo "Deployed $APP_VERSION."
    exit 0
  fi
  sleep 2
done
echo "The API didn't answer https://$api_domain/api/health/ in a minute. Look at: docker compose logs --tail 100 api" >&2
exit 1
