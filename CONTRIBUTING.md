# Contributing to Whisper

Thanks for your interest in contributing! This document explains how to get set up and what we expect from contributions.

## Development setup

```bash
git clone https://github.com/mramitdas/whisper.git
cd whisper
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
```

Or with Docker (no local Python needed):

```bash
cp .env.example .env   # set BOT_TOKEN and OWNER_ID
docker compose up -d --build
docker compose run --rm whisper alembic upgrade head
```

## Quality gates

Every PR must pass all three locally before it is ready for review:

```bash
ruff check .           # lint
mypy whisper           # type check
pytest                 # tests (58+ tests, uses fakeredis + sqlite — no external services)
```

CI runs the same gates on every push and pull request.

## Pull request process

1. **Open an issue first** for anything non-trivial (bug fix with behavior change, new feature, refactor). Small fixes (typos, CI config) can go straight to a PR.
2. **Branch from `master`**: `git checkout -b feature/my-change`.
3. **Write tests first** where it makes sense (TDD is the default workflow here). New handlers, services, and matchmaking logic all need test coverage.
4. **Keep PRs focused** — one logical change per PR. Large PRs are hard to review and slow to merge.
5. **Fill out the PR template** — link the issue, describe the change, note any privacy or security implications.
6. **Sign off on the code of conduct** — see [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md).

## What we look for in contributions

- **Correctness** — tests that prove the change works, including edge cases.
- **Privacy** — this is an anonymous chat bot. Nothing that leaks user identity, message content, or cross-user data should ever be added.
- **Simplicity** — prefer the straightforward solution. This codebase is deliberately small.
- **Style** — the existing code style is enforced by `ruff` and `mypy`; run them before committing.

## Reporting bugs

Use the [bug report template](https://github.com/mramitdas/whisper/issues/new?template=bug_report.yml). Include:

- What you did, what you expected, what actually happened.
- Your environment (Python version, Docker or bare metal, OS).
- Relevant logs (`docker compose logs whisper` or terminal output).

## Security issues

**Do not open a public issue for security vulnerabilities.** Follow the process in [SECURITY.md](SECURITY.md).

## Good first issues

Look for issues labeled [`good first issue`](https://github.com/mramitdas/whisper/labels/good%20first%20issue) — these are scoped, well-described, and beginner-friendly.

## License

By contributing, you agree that your contributions will be licensed under the [Apache License 2.0](LICENSE), the same license that covers the project.
