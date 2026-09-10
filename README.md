# misa.lol production project

This is the production VPS version of misa.lol. It contains the original FastAPI website, the original HTML dashboard, PostgreSQL-backed account data, and Dragonfly-backed sessions.

## Current live architecture

```text
Browser
  -> Cloudflare DNS/proxy
  -> VPS public port 80
  -> nginx
       -> app01/app02 (FastAPI website and API)
       -> /dashboard is served by FastAPI as HTML
            app/templates/pages/dashboard/index.html

app01/app02 -> prostgres_db data API -> Supabase PostgreSQL
app01/app02 -> Dragonfly sessions/cache
```

The `dashboard-ui/` directory is the newer Next.js dashboard copy that was previously experimented with. It is kept as inactive, recoverable code. It is not referenced by `docker-compose.yml` or `nginx/nginx.conf`; the original HTML dashboard is the active `/dashboard` route.

## Important folders

- `app/main.py` — FastAPI application and HTML/public-profile routing.
- `app/api/v1/` — authentication, user, profile, and admin API routes.
- `app/core/` — settings, sessions, security, OAuth, rate limiting, and Turnstile.
- `app/db/` — connections to PostgreSQL data API, Dragonfly, and admin database tables.
- `app/templates/pages/` — the live HTML pages, including the original dashboard.
- `app/templates/js/auth.js` — login, signup, session, username, and logout browser logic.
- `app/templates/css/` — website and dashboard styles.
- `tools/prostgres_db/` — Rust service that reads/writes users and profiles in PostgreSQL.
- `nginx/` — reverse proxy configuration.
- `docker-compose.yml` — VPS service definitions.
- `.env.example` — safe configuration template; it contains no live secrets.

## Services

The Compose services are:

- `nginx` — public HTTP reverse proxy.
- `app01` and `app02` — two FastAPI instances for basic availability.
- `prostgres_db` — Rust PostgreSQL data API. The service name is intentionally spelled this way because it is used throughout the existing Compose configuration.
- `dragonfly` — Redis-compatible session store.

There is no active Next.js dashboard service in the current production Compose file.

## Environment setup

On the VPS, from the project directory:

```bash
cd /home/ubuntu/misa
cp .env.example .env
nano .env
```

Fill these values:

```ini
DATABASE_URL=postgresql://postgres.PROJECT_REF:URL_ENCODED_PASSWORD@aws-0-REGION.pooler.supabase.com:5432/postgres
DATABASE_MAX_CONNECTIONS=10
DATA_API_KEY=one-long-random-secret

MISA_ENVIRONMENT=production
MISA_DOMAIN=misa.lol
MISA_PUBLIC_BASE_URL=https://misa.lol
MISA_CORS_ORIGINS=https://misa.lol,https://www.misa.lol

MISA_ADMIN_USER_IDS=the-user-uuid-that-is-admin

DATA_API_URL=http://prostgres_db:8080
DRAGONFLY_URL=redis://dragonfly:6379/0
```

`DATA_API_KEY` must be exactly the same for `app01`, `app02`, and `prostgres_db`. Generate one on the VPS with:

```bash
openssl rand -hex 32
```

Do not use `localhost` for `DATA_API_URL` or `DRAGONFLY_URL` inside Docker Compose. Containers use the service names above.

## Finding the admin user UUID

Log in to the website, then on the VPS run:

```bash
sudo docker exec misa-prostgres-db sh -lc 'curl -s -H "X-Data-Key: $DATA_API_KEY" http://127.0.0.1:8080/v1/users'
```

Use the account's `id` value in `MISA_ADMIN_USER_IDS`. If the data API is not published on port 8080, inspect the user through the authenticated API or PostgreSQL administration tool instead. Never make the admin check client-side only.

## Optional login providers

Email login requires Turnstile:

```ini
MISA_TURNSTILE_SITE_KEY=...
MISA_TURNSTILE_SECRET_KEY=...
```

Google, Discord, and Telegram are optional. Leave their variables empty to disable them. When enabling them, use these callback URLs:

```text
Google:   https://misa.lol/api/v1/auth/google/callback
Discord:  https://misa.lol/api/v1/auth/discord/callback
Telegram: https://misa.lol/api/v1/auth/telegram/callback
```

The Google and Discord applications must allow `https://misa.lol` as an origin where requested. Telegram must use the exact bot username configured in BotFather.

## First deployment on the VPS

Copy the project to `/home/ubuntu/misa`, create `.env`, and then run:

```bash
cd /home/ubuntu/misa
sudo docker compose config --quiet
sudo docker compose up -d --build --force-recreate --remove-orphans
sudo docker compose ps
```

Check the local website and API:

```bash
curl -I http://127.0.0.1/
curl -I http://127.0.0.1/dashboard
curl -s http://127.0.0.1/api/v1/auth/providers
```

The expected dashboard response is the original HTML page, not a Next.js page. A `302` from `/dashboard` when not logged in is expected.

## Updating the VPS

From Windows PowerShell, copy changed source files to the VPS. Example:

```powershell
$P = "C:\path\to\misa"
scp "$P\app\main.py" ubuntu@YOUR_VPS_IP:/home/ubuntu/misa/app/main.py
scp "$P\app\api\v1\profile.py" ubuntu@YOUR_VPS_IP:/home/ubuntu/misa/app/api/v1/profile.py
scp "$P\docker-compose.yml" ubuntu@YOUR_VPS_IP:/home/ubuntu/misa/docker-compose.yml
scp "$P\nginx\nginx.conf" ubuntu@YOUR_VPS_IP:/home/ubuntu/misa/nginx/nginx.conf
```

Then rebuild:

```bash
cd /home/ubuntu/misa
sudo docker compose up -d --build --force-recreate --remove-orphans app01 app02 prostgres_db nginx
sudo docker compose ps
```

`--remove-orphans` removes an old unused dashboard container if one exists. It does not delete PostgreSQL data or the Dragonfly volume.

## Cloudflare DNS

Use regular DNS records; no Cloudflare Tunnel is required for this VPS setup:

```text
Type: A
Name: @
   Content: YOUR_VPS_IP
Proxy: Proxied or DNS only

Type: CNAME
Name: www
Content: misa.lol
Proxy: Proxied or DNS only
```

For Cloudflare SSL/TLS, use `Full (strict)` after the VPS has a valid origin certificate. Cloudflare proxying can remain enabled for normal HTTP/HTTPS traffic. Do not proxy mail records.

## Database and data safety

- User accounts and saved profiles are stored in Supabase PostgreSQL through `prostgres_db`.
- Sessions are stored in Dragonfly, so restarting the app can invalidate active sessions if the session store is lost.
- Never delete the PostgreSQL or `dragonfly_data` volumes during a normal deployment.
- Back up Supabase before schema changes or migrations.
- Never place `.env`, `.env.local`, `cloudflared/cert.pem`, or provider secrets in a ZIP or repository.

## Troubleshooting

View service status:

```bash
sudo docker compose ps
sudo docker compose logs --tail=100 nginx app01 app02 prostgres_db dragonfly
```

Common issues:

- `no configuration file provided` — run `cd /home/ubuntu/misa` first.
- Cloudflare 521 — check that nginx is running and port 80 is allowed by UFW.
- Profile save returns HTML/`Unexpected token '<'` — rebuild `prostgres_db`, `app01`, `app02`, and nginx from the same project copy.
- Dashboard shows the wrong design — remove the orphan Next dashboard container and rebuild nginx/app services using this Compose file.
- Login provider fails — verify the exact callback URL, credentials, Turnstile keys, and provider status in `/api/v1/auth/providers`.

## Security checklist

1. Rotate any credentials previously shared with a former developer.
2. Keep `.env` readable only by root or the deployment user.
3. Allow only SSH, HTTP, and HTTPS through UFW.
4. Use SSH keys instead of password login where possible.
5. Keep `MISA_DEBUG=false` in production.
6. Review admin actions and audit records before enabling administrative operations.
