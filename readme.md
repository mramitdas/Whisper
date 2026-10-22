# Telegram Anonymous Chat Bot

Omegle-style anonymous 1:1 stranger chat inside Telegram. Two users get matched
in seconds, messages and media are relayed without revealing identity, and
either side can leave with one tap.

Built with **aiogram 3**, **Redis** (matchmaking + sessions) and **PostgreSQL**
(users, reports, bans — metadata only).

## Features

- Instant random matching — FIFO queue, atomic match claim (no double-pairs)
- Full media relay: text, photos, videos, voice, stickers, GIFs, documents
- Live queue position + 60s no-partner timeout with one-tap retry
- `/next`, `/stop`, `/report`, `/block` — clear exits and self-defense
- Link / @username / forbidden-word filter (kills off-platform poaching)
- Rate limiting, auto-ban after N unique reports, owner admin commands
- Idle sweep: inactive chats expire and both sides are notified
- **Zero message retention** — only metadata is stored

## Quickstart

```bash
cp .env.example .env        # set BOT_TOKEN and OWNER_ID
docker compose up -d --build
docker compose run --rm bot alembic upgrade head   # first deploy only
docker compose logs -f bot
```

## Commands

| Command | Description |
|---|---|
| `/start` | welcome + main menu |
| `/search` | join the matchmaking queue |
| `/next` | skip current partner, search again |
| `/stop` | leave the queue or the current chat |
| `/report [reason]` | report your (recent) partner |
| `/block` | block partner — never matched again |
| `/rules`, `/privacy`, `/help` | info |
| `/admin_stats` | owner: users/matches/reports/queue/bans |
| `/admin_ban <id>` / `/admin_unban <id>` | owner: manual bans |

## Development

```bash
pip install -r requirements-dev.txt
pytest           # unit tests (fakeredis + sqlite, no services needed)
ruff check .
mypy bot
```

## Config (`.env`)

| Var | Default | Purpose |
|---|---|---|
| `BOT_TOKEN` | — | Telegram bot token |
| `OWNER_ID` | — | admin user id |
| `REDIS_URL` | `redis://localhost:6379/0` | queue/sessions |
| `DATABASE_URL` | `postgresql+asyncpg://bot:bot@localhost:5432/anonbot` | metadata |
| `MATCH_TIMEOUT_SEC` | `60` | leave queue after N seconds |
| `IDLE_TIMEOUT_SEC` | `1800` | inactive chat auto-close |
| `MAX_REPORTS_BAN` | `5` | unique reports → auto-ban |
| `MSG_RATE_MAX` / `MSG_RATE_WINDOW` | `5` / `2.0` | relay flood control |
| `FORBIDDEN_WORDS` | `[]` | comma-separated filter list |

## Notes

- Long polling is used on purpose — no domain/TLS/webhook setup required.
- Sessions live in Redis with TTL: a bot restart preserves active pairs;
  a Redis flush fails safe (users return to idle with a notice).
- The matchmaking Lua script assumes standalone Redis (compose default),
  not Redis Cluster.

## Credits

Original concept by [mramitdas](https://github.com/mramitdas).
