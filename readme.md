# Whisper

**Anonymous one-on-one stranger chat, inside Telegram.**

[![CI](https://github.com/mramitdas/Whisper/actions/workflows/ci.yml/badge.svg)](https://github.com/mramitdas/Whisper/actions/workflows/ci.yml)
[![License: Apache-2.0](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](LICENSE)
[![Python 3.12+](https://img.shields.io/badge/python-3.12%2B-3776AB.svg)](https://www.python.org/downloads/)
[![Docker](https://img.shields.io/badge/docker-compose-2496ED.svg)](docker-compose.yml)
[![Code style: ruff](https://img.shields.io/badge/code%20style-ruff-261230.svg)](https://docs.astral.sh/ruff/)
[![Types: mypy](https://img.shields.io/badge/types-mypy-2A6DB2.svg)](https://mypy-lang.org/)

Whisper is a self-hosted Telegram bot for Omegle-style anonymous chat. Two people
press one button, get matched in seconds, and talk — with no names, no usernames,
and no way to find each other afterwards. Every piece of infrastructure you need
is in this repository: the bot, the matchmaking engine, the moderation layer, the
database schema, the migrations, and the deployment stack.

It is a **complete rewrite** of the original single-file bot, rebuilt for real
production traffic: atomic matchmaking under concurrency, proper rate limiting,
abuse handling, and a privacy model that stores **no message content at all**.

---

## Table of contents

- [Demo](#demo)
- [Features](#features)
- [Architecture](#architecture)
- [Privacy model](#privacy-model)
- [Quickstart](#quickstart)
- [Configuration](#configuration)
- [Commands](#commands)
- [How it works](#how-it-works)
- [Testing](#testing)
- [Deployment & operations](#deployment--operations)
- [Contributing](#contributing)
- [Security](#security)
- [Roadmap](#roadmap)
- [License](#license)
- [Credits](#credits)

---

## Demo

<!-- TODO: replace this block with a short screen recording or GIF showing
     two accounts matching, relaying a message, and using /next. -->

> **Coming soon.** A ~30 second capture of two accounts being matched, exchanging
> a message and a photo, then leaving with `/next`.
>
> Live instance: _Telegram: [@your_whisper_bot](https://t.me/your_whisper_bot)_

---

## Features

| | |
|---|---|
| **Instant matching** | FIFO queue with an atomic Lua-scripted match claim — no double-pairing, even under concurrent load. |
| **Full media relay** | Text, photos, videos, voice notes, stickers, GIFs and documents, forwarded in both directions. |
| **Queue transparency** | Live position in the queue and a one-tap retry when no partner shows up in time. |
| **One-tap exits** | `/next` skips a partner and re-queues you; `/stop` ends the conversation. |
| **Anti-poaching filter** | Links, `@usernames` and configurable forbidden words are blocked before they reach your partner. |
| **Abuse handling** | Per-user rate limits, `/report` with automatic ban thresholds, and a permanent `/block` list. |
| **Owner tooling** | `/admin_stats`, `/admin_ban` and `/admin_unban` for moderation at scale. |
| **Self-healing sessions** | Active pairs survive a bot restart (Redis TTLs); a Redis flush fails safe with a user-facing notice. |
| **Zero message retention** | Only metadata is persisted. No message body, caption, or media ever touches the database. |
| **Battery included** | Docker Compose stack with Redis 7, PostgreSQL 16, healthchecks, Alembic migrations and CI. |

---

## Architecture

```mermaid
flowchart LR
    A["User A<br/>(Telegram client)"] -->|Update| B
    C["User B<br/>(Telegram client)"] -->|Update| B
    B["Whisper<br/>aiogram 3 dispatcher<br/>middlewares: DI · DB · ban"]
    B -->|"queue · sessions · rate limits<br/>atomic Lua matchmaking"| R[("Redis 7")]
    B -->|"metadata only<br/>users · reports · bans · stats"| P[("PostgreSQL 16")]
    B -->|"relayed messages"| T["Telegram Bot API"]
    R -.->|"TTL expiry"| B
```

- **Redis** is the hot path: the matchmaking queue, live sessions, rate-limit
  counters and block lists. The match claim runs inside a Lua script, so pairing
  is atomic across every bot replica.
- **PostgreSQL** is the durable path and holds metadata only. Message content is
  never written, logged, or queued anywhere.
- The bot is stateless between requests, so it can be scaled horizontally behind
  a single Redis instance.

---

## Privacy model

Whisper's design goal is that a **conversation** is ephemeral by construction,
not by policy.

1. **No conversation content is ever stored.** The relay forwards a message to
   the partner and forgets it. No message body, caption, filename, or media is
   written to PostgreSQL, Redis, or the logs.
2. **Identity is stored, conversations are not.** The bot records your Telegram
   ID, username, display name and language code, plus a match counter and
   activity timestamps — needed for abuse handling. None of it is ever linked
   to *what was said*: that link is never created.
3. **Short-lived partner links.** A live chat is two numeric IDs in a Redis
   session with a TTL, so it expires on its own. A report stores the reporter's
   ID, the reported ID, and the free-text reason the reporter typed.
4. **No discovery.** A partner can never learn who you are, and you cannot find
   a partner again once the session ends. `/block` makes that explicit and
   permanent.
5. **Transparency for users.** `/privacy` and `/rules` state what is stored and
   why, in the bot itself.

---

## Quickstart

### Docker Compose (recommended)

```bash
git clone https://github.com/mramitdas/Whisper.git
cd whisper
cp .env.example .env          # set BOT_TOKEN and OWNER_ID
docker compose up -d --build
docker compose logs -f whisper
```

Get a token from [@BotFather](https://t.me/BotFather); `OWNER_ID` is your
numeric Telegram user ID. The stack brings up the bot, Redis and PostgreSQL with
healthchecks — no other services required. The container applies pending
database migrations on start, so there is no separate migration step.

### Local development

Requires Python 3.12+ and a reachable Redis and PostgreSQL.

```bash
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"

export BOT_TOKEN=...        # or put them in .env
export OWNER_ID=...
alembic upgrade head
python -m whisper.main      # or: whisper
```

### Running the bot

```bash
whisper                              # console script
python -m whisper.main               # equivalent
docker compose up -d whisper         # containerised
```

---

## Configuration

All configuration is environment-driven (`.env` or your orchestrator). Every
variable has a working default except the two marked as required.

| Variable | Default | Purpose |
|---|---|---|
| `BOT_TOKEN` | **required** | Telegram bot token from @BotFather. |
| `OWNER_ID` | **required** | Numeric Telegram ID of the bot owner (admin commands). |
| `REDIS_URL` | `redis://localhost:6379/0` | Redis connection string. |
| `DATABASE_URL` | `postgresql+asyncpg://bot:bot@localhost:5432/anonbot` | Async SQLAlchemy DSN. |
| `MATCH_TIMEOUT_SEC` | `60` | How long a user waits in the queue before being told no one is free. |
| `IDLE_TIMEOUT_SEC` | `1800` | Inactivity window after which a chat is closed automatically. |
| `SESSION_TTL_SEC` | `86400` | Lifetime of an active chat session in Redis. |
| `LASTPARTNER_TTL_SEC` | `3600` | How long a recent partner is remembered for `/report` and `/block`. |
| `MAX_REPORTS_BAN` | `5` | Unique reports from different users before an automatic ban. |
| `MSG_RATE_MAX` | `5` | Messages allowed per `MSG_RATE_WINDOW` seconds. |
| `MSG_RATE_WINDOW` | `2.0` | Message flood-control window, in seconds. |
| `SEARCH_RATE_MAX` | `1` | Searches allowed per `SEARCH_RATE_WINDOW` seconds. |
| `SEARCH_RATE_WINDOW` | `3.0` | Search rate-limit window, in seconds. |
| `MATCH_WINDOW` | `50` | How many queued users are scanned for a potential match. |
| `FORBIDDEN_WORDS` | `[]` | Blocked words — comma-separated (`spam,scam`) or a JSON list. |

> `FORBIDDEN_WORDS` is parsed by a custom validator, so both
> `FORBIDDEN_WORDS=spam,scam` and `FORBIDDEN_WORDS=["spam","scam"]` work.

---

## Commands

### User commands

| Command | Description |
|---|---|
| `/start` | Welcome message and main menu. |
| `/search` | Join the matchmaking queue. |
| `/next` | Skip the current partner and search again. |
| `/stop` | Leave the queue or end the current chat. |
| `/report [reason]` | Report your recent partner (optional reason is stored as metadata). |
| `/block` | Block your partner permanently — you will never be matched again. |
| `/rules` | Community rules. |
| `/privacy` | What is stored, and what is not. |
| `/help` | Command reference. |

### Owner commands

| Command | Description |
|---|---|
| `/admin_stats` | Users, matches, reports, queue depth and active bans. |
| `/admin_ban <user_id>` | Ban a user and tear down any live session. |
| `/admin_unban <user_id>` | Lift a ban. |

---

## How it works

**Matching.** A user joining the queue is pushed onto a Redis sorted set scored
by join time. Matchmaking runs as a single Lua script: it pops the oldest
waiting user, creates a session with a TTL, and returns the pairing. Because
the whole operation is atomic, two users can never be handed to the same
partner, and a bot crash mid-match cannot leave a half-created session.

**Sessions.** A live chat is two user IDs plus a small metadata blob in Redis
with `SESSION_TTL_SEC`. The bot keeps no state in memory, so restarts and
deploys are transparent to users.

**Moderation.** Every outgoing message passes through the moderation filter
(links, `@usernames`, forbidden words) and a sliding-window rate limiter before
it is relayed. Reports are counted per unique reporter; crossing
`MAX_REPORTS_BAN` applies an automatic ban, tears down the reported user's live
session, and notifies their partner that the chat ended.

**Idle sweep.** A background task closes conversations that have been silent
for longer than `IDLE_TIMEOUT_SEC` and notifies both sides.

---

## Testing

```bash
pytest           # 58 unit/integration tests
ruff check .     # linting
mypy whisper     # type checking
```

The test suite needs **no external services** — Redis is emulated with
`fakeredis` (including Lua execution) and the database with in-memory SQLite.
CI runs the same three gates on every push and pull request.

### End-to-end checklist

Full E2E requires a real bot token and two Telegram accounts. Verify:

- [ ] `/start`, `/help`, `/rules`, `/privacy` respond correctly
- [ ] `/search` with no partner times out after `MATCH_TIMEOUT_SEC` and offers a retry
- [ ] Two accounts searching simultaneously are matched
- [ ] Text and every media type relay in both directions
- [ ] `/next` re-queues and re-matches; `/stop` notifies the partner
- [ ] Rapid messages trip the flood control
- [ ] Links and `@usernames` are blocked
- [ ] `/block` prevents future matches
- [ ] `/admin_stats`, `/admin_ban`, `/admin_unban` behave correctly
- [ ] Restarting the bot mid-chat preserves the pair
- [ ] The database contains metadata only — no message content

---

## Deployment & operations

- **Migrations** are managed by Alembic. The container entrypoint runs
  `alembic upgrade head` before the bot starts, so deployments are always on the
  current schema. For manual (non-Docker) deployments, run
  `alembic upgrade head` yourself; `alembic revision --autogenerate` creates a
  new migration.
- **Healthchecks** are wired for Redis and PostgreSQL in `docker-compose.yml`;
  the bot waits for both to be healthy before starting.
- **Scaling**: the bot is stateless, so you can run several replicas against
  one Redis and one PostgreSQL. The matchmaking Lua script uses dynamic keys and
  therefore targets **standalone Redis**, not Redis Cluster.
- **Backups**: only the PostgreSQL volume holds anything worth backing up.
  Message content does not exist anywhere, by design.
- **Logs** contain startup information and unhandled errors only — never
  message content.

---

## Contributing

Contributions are welcome. Please read [CONTRIBUTING.md](CONTRIBUTING.md) for the
development setup, the quality gates every pull request must pass, and the
privacy expectations we hold to. Participation is governed by the
[Code of Conduct](CODE_OF_CONDUCT.md).

---

## Security

Please **do not** report vulnerabilities through public issues. See
[SECURITY.md](SECURITY.md) for private disclosure instructions.

---

## Roadmap

- [ ] Web admin dashboard for moderation and analytics
- [ ] Optional locale-based matchmaking preferences
- [ ] Prometheus metrics endpoint
- [ ] End-to-end test harness against the Telegram Bot API

---

## License

Whisper is open source software licensed under the
[Apache License 2.0](LICENSE).

```
Copyright 2026 Amit Das
Licensed under the Apache License, Version 2.0.
```

---

## Credits

The original concept and the legacy implementation of this bot are by
[mramitdas](https://github.com/mramitdas). Whisper is a ground-up rewrite of
that project, released under the Apache 2.0 license.
