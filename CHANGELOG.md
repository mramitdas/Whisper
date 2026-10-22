# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2026-10-22

Initial public release. Complete rewrite of the original single-file bot as a production-grade service.

### Added

- **Instant random matching** — atomic Lua-scripted matchmaking on Redis with FIFO queue, no double-pairing under concurrency.
- **Full media relay** — text, photos, videos, voice notes, stickers, GIFs, and documents forwarded anonymously in both directions.
- **Queue UX** — live position updates and a 60-second no-partner timeout with one-tap retry.
- **Conversation commands** — `/next` to skip and re-search, `/stop` to leave queue or chat.
- **Safety tools** — `/report` (auto-ban after 5 unique reports), `/block` (never rematched), link and @username filtering, configurable forbidden-word list.
- **Rate limiting** — per-user message flood control with configurable window and threshold.
- **Idle sweep** — inactive chats expire after a configurable timeout; both sides are notified.
- **Admin commands** — `/admin_stats`, `/admin_ban`, `/admin_unban` for the bot owner.
- **Zero message retention** — only metadata (users, reports, bans, aggregate stats) is stored in PostgreSQL; no message content is ever persisted.
- **Session persistence** — active pairs survive bot restarts via Redis TTLs; a Redis flush fails safe (users return to idle with a notice).
- **Ops** — Docker Compose stack (bot + Redis 7 + PostgreSQL 16) with healthchecks, Alembic migrations, GitHub Actions CI (ruff, mypy, pytest on Python 3.12).

### Changed

- **Project renamed** from Telegram_AnonymousChatBot to **Whisper**.
- **Stack rewritten** from Python-telegram-bot v13 + gino + raw Redis commands to **aiogram 3 + SQLAlchemy 2 (async) + Redis-py** with atomic Lua matchmaking.
- **Packaging** migrated to `pyproject.toml` (hatchling); `requirements.txt` / `requirements-dev.txt` removed in favor of `pip install .[dev]`.
- **Package layout** renamed from `bot/` to `whisper/`.
- **Deployments are self-migrating**: the container entrypoint runs `alembic upgrade head` before the bot starts, and the Compose project name is pinned to `whisper` so images are named consistently regardless of the checkout directory.

### Fixed

- `greenlet` is now installed on every platform via the `SQLAlchemy[asyncio]` extra — fresh installs on Apple Silicon previously failed at runtime.
- The bot no longer crash-loops when the database schema is missing; it reports the missing migration instead.
- The Telegram HTTP session is closed on startup failures, removing `Unclosed client session` noise.

### Removed

- Legacy single-file bot (`app.py`, `database.py`, `info.py`) and the old synchronous stack.
- Persistent message storage — replaced by pure relay with zero retention.

[1.0.0]: https://github.com/mramitdas/Whisper/releases/tag/v1.0.0
