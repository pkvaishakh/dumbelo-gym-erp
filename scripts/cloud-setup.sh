#!/usr/bin/env bash
# Gets a Claude Code cloud session (Linux) ready: API venv + demo gym on SQLite, web packages.
# Runs from the SessionStart hook in .claude/settings.json; does nothing on your own machine.
set -euo pipefail

[ "${CLAUDE_CODE_REMOTE:-}" = "true" ] || exit 0

ROOT="${CLAUDE_PROJECT_DIR:-$(cd "$(dirname "$0")/.." && pwd)}"

# API: no Postgres in the cloud, so .env leaves out DATABASE_URL and Django falls back to SQLite.
cd "$ROOT/api"
if [ ! -f .env ]; then
  grep -v '^DATABASE_URL=' .env.example > .env
fi
if [ ! -d .venv ]; then
  python3 -m venv .venv
fi
.venv/bin/pip install -q -r requirements-dev.txt
.venv/bin/python manage.py migrate --noinput
.venv/bin/python manage.py seed_demo || echo "seed_demo skipped (demo gym already there?)"

# Later shell commands in the session use the venv's python, pytest and manage.py.
if [ -n "${CLAUDE_ENV_FILE:-}" ]; then
  echo "export PATH=\"$ROOT/api/.venv/bin:\$PATH\"" >> "$CLAUDE_ENV_FILE"
fi

# Web
cd "$ROOT/web"
if [ ! -f .env.local ]; then
  cp .env.example .env.local
fi
npm ci --no-audit --no-fund

echo "Cloud setup done: API on SQLite with the demo gym, web packages installed."
