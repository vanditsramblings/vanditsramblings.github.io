#!/usr/bin/env python3
"""
sync_ghost_config.py — Sync Ghost site settings with a local manifest.

Usage:
    python3 scripts/sync_ghost_config.py \
        --ghost-url http://localhost:2368 \
        --api-key <id>:<secret> \
        --manifest ghost-manifest.json
"""

import argparse
import datetime
import json
import os
import sys
import jwt
import requests

def _generate_ghost_token(api_key: str) -> str:
    """Return a short-lived Ghost Admin API JWT derived from the API key."""
    try:
        key_id, secret_hex = api_key.split(":", 1)
    except ValueError:
        print("ERROR: API key must be in 'id:hex_secret' format.", file=sys.stderr)
        sys.exit(1)

    iat = int(datetime.datetime.now(datetime.timezone.utc).timestamp())
    payload = {
        "iat": iat,
        "exp": iat + 300,
        "aud": "/admin/",
    }
    token = jwt.encode(
        payload,
        bytes.fromhex(secret_hex),
        algorithm="HS256",
        headers={"kid": key_id},
    )
    return token if isinstance(token, str) else token.decode()

def _get_ghost_settings(ghost_url: str, token: str):
    url = f"{ghost_url.rstrip('/')}/ghost/api/admin/settings/"
    resp = requests.get(
        url,
        headers={"Authorization": f"Ghost {token}"},
        timeout=10
    )
    resp.raise_for_status()
    return resp.json()["settings"]

def _update_ghost_settings(ghost_url: str, token: str, settings_list: list):
    url = f"{ghost_url.rstrip('/')}/ghost/api/admin/settings/"
    resp = requests.post(
        url,
        headers={
            "Authorization": f"Ghost {token}",
            "Content-Type": "application/json"
        },
        json={"settings": settings_list},
        timeout=10
    )
    resp.raise_for_status()
    return resp.json()["settings"]

def _activate_theme(ghost_url: str, token: str, theme_name: str):
    url = f"{ghost_url.rstrip('/')}/ghost/api/admin/themes/{theme_name}/activate/"
    resp = requests.put(
        url,
        headers={"Authorization": f"Ghost {token}"},
        timeout=10
    )
    if resp.status_code == 404:
        print(f"WARNING: Theme '{theme_name}' not found. Make sure it is uploaded first.")
        return False
    resp.raise_for_status()
    print(f"SUCCESS: Theme '{theme_name}' activated.")
    return True

def sync_config(ghost_url: str, api_key: str, manifest_path: str, dry_run: bool):
    if not os.path.exists(manifest_path):
        print(f"ERROR: Manifest file not found at {manifest_path}")
        sys.exit(1)

    with open(manifest_path, 'r') as f:
        manifest = json.load(f)

    token = _generate_ghost_token(api_key)
    
    # Mapping manifest keys to Ghost settings keys
    settings_to_update = []
    
    site = manifest.get("site", {})
    if "title" in site:
        settings_to_update.append({"key": "title", "value": site["title"]})
    if "description" in site:
        settings_to_update.append({"key": "description", "value": site["description"]})
    if "navigation" in site:
        settings_to_update.append({"key": "navigation", "value": json.dumps(site["navigation"])})
    if "secondary_navigation" in site:
        settings_to_update.append({"key": "secondary_navigation", "value": json.dumps(site["secondary_navigation"])})
    
    design = manifest.get("design", {})
    if "brand_color" in design:
        settings_to_update.append({"key": "accent_color", "value": design["brand_color"]})

    if dry_run:
        print("DRY RUN: Would update the following settings:")
        for s in settings_to_update:
            print(f"  {s['key']}: {s['value']}")
        if "theme" in site:
            print(f"  Activate Theme: {site['theme']}")
    else:
        print(f"Updating {len(settings_to_update)} settings...")
        _update_ghost_settings(ghost_url, token, settings_to_update)
        print("Settings updated successfully.")
        
        if "theme" in site:
            _activate_theme(ghost_url, token, site["theme"])

def main():
    parser = argparse.ArgumentParser(description="Sync Ghost config with manifest.")
    parser.add_argument("--ghost-url", default=os.getenv("GHOST_ADMIN_URL", "http://localhost:2368"))
    parser.add_argument("--api-key", default=os.getenv("GHOST_ADMIN_API_KEY"))
    parser.add_argument("--manifest", default="ghost-manifest.json")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    if not args.api_key:
        print("ERROR: --api-key or GHOST_ADMIN_API_KEY environment variable is required.")
        sys.exit(1)

    sync_config(args.ghost_url, args.api_key, args.manifest, args.dry_run)

if __name__ == "__main__":
    main()
