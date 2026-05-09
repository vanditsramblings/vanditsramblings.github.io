#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

CONTAINER_NAME="ghost-local"
CONTENT_VOLUME="ghost_local_content"
HOST_PORT="2368"
GHOST_IMAGE="ghost:5-alpine"
GHOST_URL="http://localhost:${HOST_PORT}"
THEME_DIR="$(pwd)/ghost-theme/senior-intern"

# Remove any stale container from a previous run.
docker rm -f "${CONTAINER_NAME}" >/dev/null 2>&1 || true

# Ghost runs with SQLite by default when no MySQL environment variables are set.
# The content volume keeps themes, images, and the local database files between runs.
exec docker run -it --rm \
  --name "${CONTAINER_NAME}" \
  -p "${HOST_PORT}:2368" \
  -e "url=${GHOST_URL}" \
  -e "NODE_ENV=development" \
  -e "database__client=sqlite3" \
  -v "${CONTENT_VOLUME}:/var/lib/ghost/content" \
  -v "${THEME_DIR}:/var/lib/ghost/content/themes/senior-intern" \
  "${GHOST_IMAGE}"
