#!/usr/bin/env bash
# backup.sh — Phase 5: Export Ghost DB + content volume, push to private Git repo.
#
# What it does:
#   1. Clones (or pulls) the private backup repository.
#   2. Exports the full Ghost database via Admin API → ghost-db-export.json
#   3. Archives the Ghost content Docker volume → ghost-content.tar.gz
#   4. Commits both artefacts with a UTC timestamp and pushes to origin/main.
#
# Schedule (crontab example — daily at 02:00):
#   0 2 * * * cd /path/to/repo && bash scripts/backup.sh >> /var/log/ghost-backup.log 2>&1
#
# Prerequisites:
#   • Docker must be running with the ghost_content volume mounted.
#   • Git SSH key for BACKUP_REPO_URL must be configured (ssh-agent or deploy key).
#   • PyJWT installed: pip install PyJWT
#
# Usage:
#   source .env && bash scripts/backup.sh

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(dirname "$SCRIPT_DIR")"

# ── Config ────────────────────────────────────────────────────────────────────
GHOST_ADMIN_URL="${GHOST_ADMIN_URL:-http://localhost:2368}"
GHOST_ADMIN_API_KEY="${GHOST_ADMIN_API_KEY:?Set GHOST_ADMIN_API_KEY=id:hex_secret}"
BACKUP_REPO_URL="${BACKUP_REPO_URL:?Set BACKUP_REPO_URL=git@github.com:user/repo.git}"
GHOST_CONTENT_VOLUME="${GHOST_CONTENT_VOLUME:-ghost_content}"

BACKUP_DIR="${REPO_ROOT}/.ghost-backups"
TIMESTAMP="$(date -u +%Y%m%dT%H%M%SZ)"
SNAPSHOT_DIR="${BACKUP_DIR}/${TIMESTAMP}"

echo "=== Ghost Backup: ${TIMESTAMP} ==="
echo ""

# ── 1. Clone or update backup repository ─────────────────────────────────────
if [ ! -d "${BACKUP_DIR}/.git" ]; then
    echo "→ Cloning backup repository..."
    git clone "${BACKUP_REPO_URL}" "${BACKUP_DIR}"
else
    echo "→ Updating backup repository..."
    git -C "${BACKUP_DIR}" pull --rebase --autostash
fi

mkdir -p "${SNAPSHOT_DIR}"

# ── 2. Generate Ghost Admin API JWT ──────────────────────────────────────────
echo "→ Generating API token..."
GHOST_TOKEN=$(python3 - <<'PYEOF'
import os, datetime, jwt, sys
key = os.environ["GHOST_ADMIN_API_KEY"]
kid, secret = key.split(":", 1)
iat = int(datetime.datetime.now(datetime.timezone.utc).timestamp())
token = jwt.encode(
    {"iat": iat, "exp": iat + 300, "aud": "/admin/"},
    bytes.fromhex(secret),
    algorithm="HS256",
    headers={"kid": kid},
)
print(token if isinstance(token, str) else token.decode())
PYEOF
)

# ── 3. Export Ghost database via Admin API ────────────────────────────────────
DB_EXPORT="${SNAPSHOT_DIR}/ghost-db-export.json"
echo "→ Exporting Ghost database..."
http_code=$(curl -s -o "${DB_EXPORT}" -w "%{http_code}" \
    -H "Authorization: Ghost ${GHOST_TOKEN}" \
    "${GHOST_ADMIN_URL}/ghost/api/admin/db/")

if [ "$http_code" != "200" ]; then
    echo "  ERROR: Ghost API returned HTTP ${http_code}. Is Ghost running?"
    cat "${DB_EXPORT}" || true
    exit 1
fi

db_size=$(du -sh "${DB_EXPORT}" | cut -f1)
echo "  Saved: ${DB_EXPORT} (${db_size})"

# ── 4. Archive Ghost content volume ──────────────────────────────────────────
CONTENT_ARCHIVE="${SNAPSHOT_DIR}/ghost-content.tar.gz"
echo "→ Archiving Ghost content volume (${GHOST_CONTENT_VOLUME})..."

# Spin up a throwaway Alpine container to tar the volume without stopping Ghost
docker run --rm \
    -v "${GHOST_CONTENT_VOLUME}:/ghost-content:ro" \
    -v "${SNAPSHOT_DIR}:/backup" \
    alpine \
    tar czf /backup/ghost-content.tar.gz -C /ghost-content .

content_size=$(du -sh "${CONTENT_ARCHIVE}" | cut -f1)
echo "  Saved: ${CONTENT_ARCHIVE} (${content_size})"

# ── 5. Commit and push to private repository ─────────────────────────────────
echo "→ Committing backup..."
git -C "${BACKUP_DIR}" add -A

# Only commit if there are staged changes (idempotent re-runs)
if git -C "${BACKUP_DIR}" diff --cached --quiet; then
    echo "  Nothing new to commit."
else
    git -C "${BACKUP_DIR}" commit -m "backup: ${TIMESTAMP}"
    git -C "${BACKUP_DIR}" push origin main
    echo "  Pushed to ${BACKUP_REPO_URL}"
fi

echo ""
echo "=== Backup complete: ${TIMESTAMP} ==="
