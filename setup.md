# Ghost Setup Guide

This repository now runs a self-hosted Ghost blog. Keep this guide as the first-stop checklist for initial setup, local testing, and the small set of Ghost features we care about: posts, publishing, and email.

## 1. Initial Setup

### Local first boot
1. Start the local stack using the helper script:
   ```bash
   bash scripts/run_ghost_local.sh
   ```
   *Note: This script automatically handles cleanup and ensures a fresh environment.*
2. To stop the local stack:
   ```bash
   bash scripts/stop_ghost_local.sh
   ```
2. Open Ghost admin at `http://localhost:2368/ghost`.
3. Finish the Ghost setup wizard:
   - Site title: `Senior Intern`
   - Admin name: your name
   - Admin email: your email address
   - Admin password: choose a strong password
4. Log in and confirm the blog homepage loads at `http://localhost:2368`.

### Production first boot
1. Copy the env template:
   ```bash
   cp .env.example .env
   ```
2. Fill in all required values in `.env`.
3. Start the production stack:
   ```bash
   docker compose up -d
   ```
4. Open the site through the Cloudflare hostname, then visit `/ghost` to finish any remaining setup.

## 2. Mandatory Steps

These are the steps that must be done before the site is considered ready:

1. Set `GHOST_URL` to the final public URL.
2. Set MySQL credentials: `MYSQL_ROOT_PASSWORD`, `MYSQL_USER`, `MYSQL_PASSWORD`, `MYSQL_DATABASE`.
3. Set `CLOUDFLARE_TUNNEL_TOKEN` for production.
4. Create the first Ghost admin user during the setup wizard.
5. Activate the custom theme from Ghost Admin.
6. Create the pages you want Ghost to manage, such as `about` and `projects`.
7. Configure email before depending on password resets or notifications.

## 3. Configuration Reference

### Ghost URL
`GHOST_URL` is the public address of the site, for example `https://blog.yourdomain.com`. Ghost uses this to generate correct links.

### Database
The MySQL settings control persistence for posts, users, settings, and sessions.

- `MYSQL_ROOT_PASSWORD`: root password for the database container
- `MYSQL_USER`: Ghost database user
- `MYSQL_PASSWORD`: Ghost database password
- `MYSQL_DATABASE`: database name Ghost will use

### Cloudflare Tunnel
`CLOUDFLARE_TUNNEL_TOKEN` connects the local Ghost container to Cloudflare Zero Trust. The tunnel exposes Ghost without port forwarding.

### Email
Mail is optional for local testing, but important for production.

- `MAIL_TRANSPORT`: set to `SMTP` for a real mail provider, or `Direct` for minimal local use
- `MAIL_FROM`: sender address shown in Ghost email
- `MAIL_HOST`: SMTP server hostname
- `MAIL_PORT`: SMTP server port, usually `587`
- `MAIL_USER`: SMTP username
- `MAIL_PASS`: SMTP password or API key

### Ghost Admin API
`GHOST_ADMIN_API_KEY` is required for migration scripts and backups. Create it in Ghost Admin:

1. Go to `Settings`
2. Open `Integrations`
3. Add a custom integration
4. Copy the key in `id:secret` format into `.env`

### Backup settings
- `BACKUP_REPO_URL`: private Git repo used to store exported backups
- `GHOST_ADMIN_URL`: admin URL used by the backup script, usually `http://localhost:2368`
- `GHOST_CONTENT_VOLUME`: Docker volume name that stores Ghost content

## 4. Centralized Configuration (Manifest)

We use `ghost-manifest.json` as the source of truth for site-wide settings that aren't easily set via environment variables. This includes:
- Site Title & Description
- Primary and Secondary Navigation
- Active Theme
- Brand Accent Color

### Syncing configuration
Once Ghost is running and you have an API key, sync the manifest:
```bash
python3 scripts/sync_ghost_config.py
```

This ensures that even if the database is reset, you can restore your preferred site structure instantly.

## 5. Theme Setup

1. Start Ghost.
2. Log in to `/ghost`.
3. Go to `Settings` > `Design`.
4. Activate the `senior-intern` theme.

The theme provides the homepage, article layout, about page, and project page styling.

## 5. Adding New Blogs

Add new blog posts through Ghost Admin.

1. Go to `Posts`.
2. Click `New post`.
3. Add a title and body.
4. Use the editor to write Markdown-style content, code blocks, and images.
5. Add tags if needed.
6. Save as draft or publish immediately.

If you are migrating old content, use the migration script instead of manually recreating posts:

```bash
python3 scripts/migrate_to_ghost.py --dry-run
```

## 6. Publishing Posts

Publishing is straightforward in Ghost:

1. Create or open a post.
2. Confirm the title, slug, tags, and cover image.
3. Review the preview.
4. Click `Publish`.
5. If you need to schedule a post, choose a future publish date instead of publishing immediately.

Ghost keeps drafts until you publish them, so you can safely edit content before it goes live.

## 7. Email Configuration

Use real SMTP credentials for production. That keeps password resets and staff notifications working.

### Recommended production values
```env
MAIL_TRANSPORT=SMTP
MAIL_FROM=noreply@yourdomain.com
MAIL_HOST=smtp.sendgrid.net
MAIL_PORT=587
MAIL_USER=apikey
MAIL_PASS=your_sendgrid_api_key_here
```

### Basic rules
- Use `Direct` only if you are testing locally and do not need transactional email.
- Use a real mailbox or mail provider for production.
- Verify the sender address before relying on password reset emails.

## 8. Local Development Workflow

Use the local stack when you want to test content, theme changes, or email settings before touching the public site.

1. Start Ghost locally.
2. Import or create a small test post.
3. Check the theme appearance.
4. Verify the admin editor, post previews, and page slugs.
5. If you change the theme, refresh Ghost after updating the mounted theme folder.

## 9. Useful Commands

```bash
# Start local Ghost with MySQL
bash scripts/run_ghost_local.sh

# Stop local Ghost
bash scripts/stop_ghost_local.sh

# Production Ghost stack

docker compose up -d

# Dry-run migration from markdown to Ghost

python3 scripts/migrate_to_ghost.py --dry-run

# Upload local images to Ghost

bash scripts/migrate_assets.sh

# Run a Ghost backup

bash scripts/backup.sh
```

## 10. What We Are Not Covering Yet

This setup guide intentionally stays focused on the parts we use right now:
- blog posts
- publishing flow
- email configuration
- theme activation
- migration and backup scripts

If you later want memberships, newsletters, or comments, add those after the core blog is stable.
