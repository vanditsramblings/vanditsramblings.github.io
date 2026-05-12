#!/usr/bin/env bash
set -euo pipefail

# Get the root directory of the repository
ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "${ROOT_DIR}"

echo "Cleaning up any existing Ghost local services..."
docker compose -f docker-compose.local.yml down --remove-orphans

echo "Bootstrapping Ghost local services (Ghost + MySQL)..."
echo "Ghost will be available at http://localhost:2368"
echo "Ghost Admin: http://localhost:2368/ghost"

# Load local environment variables if present
if [ -f .env.local ]; then
  export $(grep -v '^#' .env.local | xargs)
fi

# Start services in the background
docker compose -f docker-compose.local.yml up -d

# Run the provisioning script to handle setup and theme activation
python3 scripts/run_ghost_local.py

echo "Services are ready. Following logs (Ctrl+C to stop, containers will remain running)..."
docker compose -f docker-compose.local.yml logs -f

