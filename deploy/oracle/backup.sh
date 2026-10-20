#!/usr/bin/env bash
# Writes a copy of the database to ~/backups and keeps the newest 14. Run nightly from cron (docs/deploy-oracle.md).
# A copy on the same server is not a backup on its own: download them, or send them to Object Storage.
set -euo pipefail
cd "$(dirname "$0")"

dir="$HOME/backups"
mkdir -p "$dir"
file="$dir/dumbelo-$(date -u +%Y%m%dT%H%MZ).dump"

# Written under another name first, so a dump that fails halfway is never mistaken for a good one.
docker compose exec -T db pg_dump -U dumbelo -d dumbelo --format=custom > "$file.part"
mv "$file.part" "$file"

ls -1t "$dir"/dumbelo-*.dump | tail -n +15 | xargs -r rm --
echo "$(date -u +%FT%TZ) wrote $file ($(du -h "$file" | cut -f1))"
