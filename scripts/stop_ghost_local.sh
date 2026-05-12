#!/usr/bin/env bash
set -euo pipefail

# Get the root directory of the repository
ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "${ROOT_DIR}"

echo "Stopping Ghost local services..."
docker compose -f docker-compose.local.yml down

echo "Done."
