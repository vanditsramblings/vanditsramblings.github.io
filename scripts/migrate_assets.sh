#!/usr/bin/env bash
# migrate_assets.sh — Phase 4: Copy local image assets into the Ghost content volume.
#
# This script uploads every image from public/images/ into the running Ghost
# container via the Ghost Admin API. Ghost stores the uploaded files under
# /var/lib/ghost/content/images/ and returns the final public URL.
#
# After running this script, re-run migrate_to_ghost.py with --image-base-url
# set to the value printed at the end of this script so that image references
# in your posts are rewritten to the new Ghost URLs.
#
# Prerequisites:
#   • Ghost must be running (docker compose up -d)
#   • GHOST_ADMIN_URL and GHOST_ADMIN_API_KEY must be set in your environment
#     or sourced from .env
#
# Usage:
#   source .env && bash scripts/migrate_assets.sh
#   bash scripts/migrate_assets.sh --images-dir public/images

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(dirname "$SCRIPT_DIR")"

# ── Config ────────────────────────────────────────────────────────────────────
GHOST_ADMIN_URL="${GHOST_ADMIN_URL:-http://localhost:2368}"
GHOST_ADMIN_API_KEY="${GHOST_ADMIN_API_KEY:?Set GHOST_ADMIN_API_KEY=id:hex_secret}"
IMAGES_DIR="${1:-${REPO_ROOT}/public/images}"

if [ ! -d "$IMAGES_DIR" ]; then
    echo "No images directory found at: $IMAGES_DIR"
    echo "Nothing to upload. Exiting."
    exit 0
fi

# ── Generate Ghost JWT ────────────────────────────────────────────────────────
_ghost_token() {
    python3 - <<'PYEOF'
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
}

# ── Upload images ─────────────────────────────────────────────────────────────
SUPPORTED_EXTENSIONS=("jpg" "jpeg" "png" "gif" "webp" "svg" "ico")

echo "Uploading images from: $IMAGES_DIR"
echo "Target Ghost instance: $GHOST_ADMIN_URL"
echo ""

TOKEN="$(_ghost_token)"
UPLOAD_URL="${GHOST_ADMIN_URL}/ghost/api/admin/images/upload/"

uploaded=0
failed=0

# Build a glob pattern for all supported types
shopt -s nullglob
for ext in "${SUPPORTED_EXTENSIONS[@]}"; do
    for file in "$IMAGES_DIR"/**/*."$ext" "$IMAGES_DIR"/*."$ext"; do
        [ -f "$file" ] || continue

        filename="$(basename "$file")"
        echo -n "  Uploading $filename ... "

        response=$(curl -sf \
            -H "Authorization: Ghost ${TOKEN}" \
            -F "file=@${file};type=$(file --mime-type -b "$file")" \
            -F "purpose=image" \
            "${UPLOAD_URL}" 2>&1) || {
            echo "FAILED (curl error)"
            ((failed++))
            continue
        }

        ghost_url=$(echo "$response" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('images',[{}])[0].get('url',''))" 2>/dev/null || true)
        if [ -n "$ghost_url" ]; then
            echo "OK → $ghost_url"
            ((uploaded++))
        else
            echo "FAILED: $response"
            ((failed++))
        fi
    done
done

echo ""
echo "─────────────────────────────────────────────"
echo "  Uploaded : $uploaded"
echo "  Failed   : $failed"
echo ""
echo "Next step — re-run migration with rewritten image paths:"
echo ""
echo "  python3 scripts/migrate_to_ghost.py \\"
echo "      --ghost-url ${GHOST_ADMIN_URL} \\"
echo "      --api-key \"\${GHOST_ADMIN_API_KEY}\" \\"
echo "      --image-base-url ${GHOST_ADMIN_URL}/content/images"
