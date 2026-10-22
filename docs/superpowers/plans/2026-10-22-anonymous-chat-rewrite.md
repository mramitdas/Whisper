# Anonymous Chat Bot Rewrite — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the legacy single-file bot with a production-grade anonymous 1:1 matching bot (aiogram 3 + Redis + PostgreSQL) ready for public launch.

**Architecture:** aiogram 3 dispatcher with routers/middlewares; Redis holds the FIFO queue (ZSET), atomic Lua match claim, sessions (TTL), rate limits, blocklists, and active bans; PostgreSQL stores users, reports, bans (metadata only — zero message content). Bot runs in long-polling mode under Docker Compose with Redis 7 + Postgres 16.

**Tech Stack:** Python 3.12+, aiogram 3.x, redis-py (async), SQLAlchemy 2 async + asyncpg + Alembic, pydantic-settings, pytest + pytest-asyncio + fakeredis + aiosqlite, ruff, mypy, Docker Compose.

---

## File Structure

```
bot/
  __init__.py
  main.py            # entrypoint: wiring, middleware, jobs, polling
  config.py          # Settings (pydantic-settings)
  texts.py           # ALL user-facing strings
  keyboards.py       # reply + inline keyboards
  di.py              # DI + DB-session + ban middlewares
  errors.py          # global error handler
  jobs.py            # queue-position task, idle sweeper
  redis_client.py
  db/
    __init__.py
    base.py          # Base, TimestampMixin, utcnow
    models.py        # User, Report, Ban, Stat
    repo.py          # async CRUD
  services/
    __init__.py
    matchmaker.py    # Lua script + queue ops
    sessions.py      # session/lastpartner/act keys
    ratelimit.py     # sliding-window + fixed-window
    moderation.py    # content filter
    reporting.py     # submit_report + add_block
    bans.py          # Redis ban set + DB sync
  handlers/
    __init__.py      # register_all(dp)
    start.py         # /start, rules/privacy/help
    chat.py          # /search /next /stop + buttons
    relay.py         # text + media relay (last)
    report.py        # /report /block
    admin.py         # /admin_* owner-gated
alembic/  alembic.ini  versions/0001_initial.py
tests/    conftest.py, test_{config,repo,sessions,matchmaker,ratelimit,moderation,bans,handlers,jobs,relay,reporting,admin,errors,main_wiring}.py
Dockerfile  docker-compose.yml  .env.example  requirements.txt  requirements-dev.txt
pyproject.toml      # tool config only (ruff/mypy/pytest)
.github/workflows/ci.yml
```

Legacy `app.py`, `database.py`, `info.py` are deleted in the final task.

**Session state contract (Redis keys):**
- `queue:waiting` — ZSET, score = enqueue time (FIFO)
- `session:{uid}` → partner uid, TTL = session_ttl
- `lastpartner:{uid}` → partner uid, TTL 1h (post-chat report target)
- `act:{uid}` — idle marker, TTL = idle_timeout (refreshed on relay)
- `blocks:{uid}` — SET of blocked uids
- `bans:active` — SET of banned uids
- `rl:{bucket}:{uid}` — rate-limit keys

---

### Task 1: Scaffold + config + tooling

**Files:** `pyproject.toml`, `requirements.txt`, `requirements-dev.txt`, `.env.example`, `.gitignore` (modify), `bot/__init__.py`, `bot/config.py`, `bot/texts.py`, `bot/keyboards.py`, `tests/test_config.py`

- [x] Write failing `tests/test_config.py` (defaults + env override), run → FAIL
- [x] Create requirements, pyproject tool config, `Settings`, `texts.py` (all user-facing strings), `keyboards.py` (main/chat/cancel/search-again keyboards)
- [x] `pip install -r requirements-dev.txt && pytest tests/test_config.py -v` → PASS
- [x] `ruff check .` clean → commit `feat: scaffold config, texts, keyboards, tooling`

### Task 2: Database layer

**Files:** `bot/db/{__init__,base,models,repo}.py`, `alembic.ini`, `alembic/env.py`, `alembic/versions/0001_initial.py`, `tests/conftest.py`, `tests/test_repo.py`

- [x] Write failing tests (upsert, reports/unique_reporters, ban lifecycle, counters) → FAIL
- [x] Implement models User/Report/Ban/Stat + repo CRUD (flush-based, typed)
- [x] pytest → PASS; hand-write Alembic initial migration matching models
- [x] commit `feat: postgres models, repo, alembic migration`

### Task 3: Redis client + session service

**Files:** `bot/redis_client.py`, `bot/services/__init__.py`, `bot/services/sessions.py`, `tests/test_sessions.py`

- [x] Failing tests: get_partner, destroy (sets lastpartner, clears act, idempotent), report target preference, touch_act → FAIL
- [x] Implement → PASS → commit `feat: redis session service`

### Task 4: Matchmaking engine (Lua atomic claim)

**Files:** `bot/services/matchmaker.py`, `tests/test_matchmaker.py`

- [x] Failing tests: FIFO match, unmatched stays queued, never self-match, blocklist skip, session TTL, dequeue/position → FAIL
- [x] Implement `enqueue_and_match` (ZADD self + scan window of oldest candidates + blocklist SISMEMBER both ways + ZREM pair + SET session keys with TTL, all atomic in one EVAL), `dequeue`, `queue_position`, `queue_size`
- [x] pytest → PASS → commit `feat: atomic lua matchmaking with blocklist + ttl sessions`

### Task 5: Rate limiters

**Files:** `bot/services/ratelimit.py`, `tests/test_ratelimit.py`

- [x] Failing tests: sliding allows max then blocks (per-user/bucket isolation), fixed window resets → FAIL
- [x] Implement `allow_sliding` (ZSET timestamps + unique member) and `allow_fixed` (INCR+EXPIRE) → PASS → commit

### Task 6: Content moderation filter

**Files:** `bot/services/moderation.py`, `tests/test_moderation.py`

- [x] Failing tests: @username (≥5 chars) blocked, short @ allowed, http/https/t.me/www blocked, emails/decimals allowed, forbidden words case-insensitive → FAIL
- [x] Implement `check_text(text, forbidden_words) -> "link"|"forbidden"|None` → PASS → commit

### Task 7: Ban service + middlewares

**Files:** `bot/services/bans.py`, `bot/di.py`, `tests/test_bans.py`

- [x] Failing tests: ban roundtrip via Redis set + DB, load_bans from DB → FAIL
- [x] Implement bans service (is_banned/add_ban/remove_ban/active_ban_count/load_bans)
- [x] Implement DiMiddleware (settings/redis/sessionmaker into handler data), DbMiddleware (session per update, commit after), BanMiddleware (skip handlers + reply for banned)
- [x] pytest → PASS → commit `feat: ban service and DI/DB/ban middlewares`

### Task 8: start/help/rules/privacy handlers

**Files:** `bot/handlers/__init__.py`, `bot/handlers/start.py`, placeholder routers for admin/report/chat/relay, `tests/test_handlers.py`

- [x] Failing tests with duck-typed FakeMessage: start welcomes + upserts; banned user gets suspension notice → FAIL
- [x] Implement `cmd_start` (ban gate → upsert → welcome + main keyboard), `/help`, `/rules`, `/privacy` + Rules/Privacy buttons
- [x] `register_all(dp)` orders routers: start, admin, report, chat, relay (relay last) → PASS → commit

### Task 9: Search flow — queue, position job, cancel, timeout

**Files:** `bot/jobs.py`, `bot/handlers/chat.py`, `tests/test_jobs.py`

- [x] Failing tests: searching_task exits when matched; times out at 0s → dequeued + "No one's free" edit → FAIL
- [x] Implement jobs (search_tasks dict, start/cancel, searching_task loop: 1s tick, ZRANK check, timeout dequeue, edit position)
- [x] Implement chat.py: do_search (already-chatting gate, fixed-window throttle, enqueue_and_match, notify both + chat keyboard, else start job), `/search` + Find partner button, `/stop` + Stop (leave queue or destroy session), `/next` (destroy + re-search), cancel_search / search_again callbacks
- [x] pytest → PASS → commit `feat: search/next/stop flow with live queue position and timeout`

### Task 10: Message + media relay

**Files:** `bot/handlers/relay.py`, `tests/test_relay.py`

- [x] Failing tests: text relayed to partner; no-session notice; link blocked (nothing delivered to partner); flood dropped (≤ max delivered); photo caption filtered → FAIL
- [x] Implement relay_message: partner lookup → sliding-window rate limit → content filter (text or caption) → touch_act → typed _deliver for each media type
- [x] Routers: `F.text` and media filter handlers → PASS → commit

### Task 11: Report + block (auto-ban)

**Files:** `bot/services/reporting.py`, `bot/handlers/report.py`, `tests/test_reporting.py`

- [x] Failing tests: auto-ban at threshold of unique reporters; same reporter counts once; block prevents rematch → FAIL
- [x] Implement submit_report (store + unique count ≥ threshold → add_ban) and add_block
- [x] Implement /report (target = live session else lastpartner; reason from text; on auto-ban disconnect target) and /block → PASS → commit

### Task 12: Admin commands

**Files:** `bot/handlers/admin.py`, `tests/test_admin.py`

- [x] Failing tests: stats denied for non-owner, shown for owner; admin_ban/admin_unban roundtrip → FAIL
- [x] Implement owner-gated `/admin_stats`, `/admin_ban <id>`, `/admin_unban <id>` → PASS → commit

### Task 13: Error handler + idle sweeper

**Files:** `bot/errors.py`, append to `bot/jobs.py`, `tests/test_errors.py`

- [x] Failing test: idle_sweeper_once drops inactive pair and notifies both → FAIL
- [x] Implement sweeper (SCAN session:* without act → destroy + notify) and periodic loop
- [x] Implement on_error: RetryAfter → sleep; ForbiddenError → destroy session + notify partner; else log + friendly message → PASS → commit

### Task 14: Entrypoint wiring

**Files:** `bot/main.py`, `tests/test_main_wiring.py`

- [x] Failing test: register_all order == [start, admin, report, chat, relay] → FAIL
- [x] Implement main(): Settings, redis, engine/sessionmaker, Bot, Dispatcher, three outer middlewares, register_all, error handler (async wrapper), load_bans on startup, idle sweeper task, start_polling, cleanup in finally → PASS → commit

### Task 15: Docker, compose, README

**Files:** `Dockerfile`, `docker-compose.yml`, `.dockerignore`, `readme.md` (rewrite)

- [x] Dockerfile python:3.12-slim; compose: bot + redis:7-alpine + postgres:16-alpine with healthchecks, pgdata volume, env_file
- [x] README: quickstart, alembic first-deploy step, commands table, privacy stance, dev commands
- [x] `docker compose config` valid; `docker compose build` succeeds → commit

### Task 16: CI + remove legacy files + full verify

**Files:** `.github/workflows/ci.yml`; delete `app.py`, `database.py`, `info.py`

- [x] CI: ruff check, mypy, pytest on push/PR (no services needed — fakeredis + aiosqlite)
- [x] Delete legacy files; grep for stale imports
- [x] Full verify: `pytest -v && ruff check . && mypy bot` all clean → commit

---

## Known plan corrections (fixed during implementation)

1. Task 11: no inline imports in `report.py` — `from aiogram import F, Router` at top.
2. Task 13: `idle_sweeper_once(redis, bot)` signature used in both code and test.
3. Task 14: error handler registered as `async def _err(event): await on_error(event, bot, redis, settings)`.
4. Task 2: migration hand-written (no dev Postgres guaranteed); `alembic/env.py` imports `bot.db.models`.
5. `bot/db/__init__.py` imports models so `Base.metadata` is populated for Alembic.
