#!/usr/bin/env python3
"""
migrate_to_ghost.py — Migrate Markdown posts to Ghost via Admin API.

Phase 3: Reads Markdown files, preserves original publication dates, posts via API.
Phase 4: Rewrites local image paths to Ghost content URLs (--image-base-url).

Usage:
    # Dry run — preview what will be migrated
    python3 scripts/migrate_to_ghost.py --dry-run

    # Migrate to local Ghost instance
    python3 scripts/migrate_to_ghost.py \
        --ghost-url http://localhost:2368 \
        --api-key <id>:<secret>

    # Migrate with image path rewriting
    python3 scripts/migrate_to_ghost.py \
        --ghost-url http://localhost:2368 \
        --api-key <id>:<secret> \
        --image-base-url https://blog.yourdomain.com/content/images

Prerequisites:
    pip install requests python-frontmatter PyJWT Markdown

Ghost Admin API key:
    Ghost Admin → Settings → Integrations → Add custom integration → copy key.
    Format: {key_id}:{hex_secret}
"""

import argparse
import datetime
import glob
import os
import re
import sys

import frontmatter
import jwt          # PyJWT
import markdown as md_lib
import requests


# ── Auth ──────────────────────────────────────────────────────────────────────

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
        "exp": iat + 300,   # 5-minute window is plenty for a migration run
        "aud": "/admin/",
    }
    token = jwt.encode(
        payload,
        bytes.fromhex(secret_hex),
        algorithm="HS256",
        headers={"kid": key_id},
    )
    # PyJWT >= 2.0 returns str directly; older versions return bytes
    return token if isinstance(token, str) else token.decode()


# ── Content conversion ────────────────────────────────────────────────────────

_IMAGE_PATTERN = re.compile(r"!\[([^\]]*)\]\(([^)]+)\)")


def _rewrite_images(content: str, image_base_url: str) -> str:
    """Rewrite relative image paths in Markdown to absolute Ghost content URLs."""
    base = image_base_url.rstrip("/")

    def _replace(match: re.Match) -> str:
        alt, path = match.group(1), match.group(2)
        if path.startswith(("http://", "https://", "//")):
            return match.group(0)               # already absolute — leave alone
        # Strip leading /public or /assets prefixes from imported Markdown paths
        path = re.sub(r"^/?(public|assets)/", "", path)
        return f"![{alt}]({base}/{path.lstrip('/')})"

    return _IMAGE_PATTERN.sub(_replace, content)


def _to_html(content: str, image_base_url: str | None) -> str:
    """Convert Markdown to HTML, optionally rewriting image paths first."""
    if image_base_url:
        content = _rewrite_images(content, image_base_url)
    converter = md_lib.Markdown(
        extensions=["fenced_code", "tables", "nl2br", "sane_lists"],
    )
    return converter.convert(content)


# ── Post loading ──────────────────────────────────────────────────────────────

def _load_posts(blog_dir: str) -> list[tuple[str, frontmatter.Post]]:
    pattern = os.path.join(blog_dir, "*.md")
    files = sorted(glob.glob(pattern))
    if not files:
        print(f"No .md files found in: {blog_dir}", file=sys.stderr)
        sys.exit(1)
    return [(f, frontmatter.load(f)) for f in files]


def _iso_date(value) -> str | None:
    """Normalise a frontmatter date/datetime value to ISO 8601 with UTC timezone."""
    if value is None:
        return None
    if isinstance(value, datetime.datetime):
        if value.tzinfo is None:
            value = value.replace(tzinfo=datetime.timezone.utc)
        return value.isoformat()
    if isinstance(value, datetime.date):
        return datetime.datetime(
            value.year, value.month, value.day, tzinfo=datetime.timezone.utc
        ).isoformat()
    return None


# ── Ghost API ─────────────────────────────────────────────────────────────────

def _post_to_ghost(
    ghost_url: str,
    api_key: str,
    payload: dict,
) -> dict:
    """Create a single post via Ghost Admin API. Returns the created post object."""
    token = _generate_ghost_token(api_key)
    url = f"{ghost_url.rstrip('/')}/ghost/api/admin/posts/"
    resp = requests.post(
        url,
        headers={
            "Authorization": f"Ghost {token}",
            "Content-Type": "application/json",
        },
        json={"posts": [payload]},
        timeout=30,
    )
    resp.raise_for_status()
    return resp.json()["posts"][0]


# ── Main migration ────────────────────────────────────────────────────────────

def migrate(
    ghost_url: str,
    api_key: str,
    blog_dir: str,
    image_base_url: str | None,
    dry_run: bool,
) -> None:
    posts = _load_posts(blog_dir)
    print(f"Found {len(posts)} posts in '{blog_dir}'.\n")

    succeeded, failed = [], []

    for filepath, post in posts:
        filename = os.path.basename(filepath)
        title = post.get("title", "Untitled")
        published_at = _iso_date(post.get("publishDate"))
        tags = [{"name": t} for t in post.get("tags", [])]
        html = _to_html(post.content, image_base_url)

        label = "DRY RUN" if dry_run else "MIGRATE"
        print(f"[{label}] {title}")
        print(f"  File:      {filename}")
        print(f"  Published: {published_at or '(none)'}")
        print(f"  Tags:      {[t['name'] for t in tags]}")
        print(f"  HTML len:  {len(html)} chars")

        if dry_run:
            succeeded.append(title)
            print()
            continue

        ghost_payload = {
            "title": title,
            "html": html,
            "status": "published",
            "tags": tags,
        }
        if published_at:
            ghost_payload["published_at"] = published_at

        try:
            created = _post_to_ghost(ghost_url, api_key, ghost_payload)
            print(f"  Created:   {created.get('url', created.get('id'))}")
            succeeded.append(title)
        except requests.HTTPError as exc:
            print(f"  ERROR {exc.response.status_code}: {exc.response.text[:200]}")
            failed.append(title)
        except Exception as exc:  # noqa: BLE001
            print(f"  ERROR: {exc}")
            failed.append(title)
        print()

    print("─" * 50)
    print(f"  Succeeded : {len(succeeded)}")
    print(f"  Failed    : {len(failed)}")
    if failed:
        print(f"  Failed posts: {failed}")
        sys.exit(1)


# ── CLI ───────────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Migrate Markdown blog posts to Ghost via Admin API.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "--ghost-url",
        default=os.getenv("GHOST_ADMIN_URL", "http://localhost:2368"),
        help="Ghost base URL (default: GHOST_ADMIN_URL or http://localhost:2368)",
    )
    parser.add_argument(
        "--api-key",
        default=os.getenv("GHOST_ADMIN_API_KEY"),
        help="Ghost Admin API key in id:hex_secret format (or set GHOST_ADMIN_API_KEY)",
    )
    parser.add_argument(
        "--blog-dir",
        default="src/content/blog",
        help="Path to the markdown blog content directory (default: src/content/blog)",
    )
    parser.add_argument(
        "--image-base-url",
        default=None,
        help=(
            "Base URL for rewriting relative image paths, e.g. "
            "https://blog.yourdomain.com/content/images. "
            "Also upload images to that Ghost path first (see Phase 4 in the spec)."
        ),
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Parse and print posts without sending anything to Ghost.",
    )
    args = parser.parse_args()

    if not args.dry_run and not args.api_key:
        parser.error(
            "--api-key / GHOST_ADMIN_API_KEY is required for a live migration.\n"
            "Create a Custom Integration in Ghost Admin → Settings → Integrations."
        )

    migrate(
        ghost_url=args.ghost_url,
        api_key=args.api_key or "placeholder:00",
        blog_dir=args.blog_dir,
        image_base_url=args.image_base_url,
        dry_run=args.dry_run,
    )


if __name__ == "__main__":
    main()
