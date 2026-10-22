# Security Policy

## Supported Versions

Only the latest code on the `master` branch receives security updates. There are no versioned release branches yet.

| Version | Supported          |
| ------- | ------------------ |
| master  | :white_check_mark: |

## Reporting a Vulnerability

**Please do not report security vulnerabilities through public GitHub issues.**

Instead, report them privately via one of these channels:

- **GitHub Security Advisories** (preferred): [Report a vulnerability](https://github.com/mramitdas/Whisper/security/advisories/new)
- **Email**: [mramitdas99@gmail.com](mailto:mramitdas99@gmail.com)

Include as much detail as you can:

- The type of vulnerability (e.g., injection, auth bypass, privacy leak, DoS).
- Steps to reproduce the issue.
- The potential impact — especially anything involving user identity, message content, or cross-user data leakage.
- Any suggested fix or patch, if you have one.

## What to expect

- **Acknowledgement** within **72 hours**.
- **Initial assessment** within **7 days** — we will confirm the issue and estimate severity.
- **Fix timeline** depends on severity: critical issues are patched as fast as possible; lower-severity issues are scheduled into the next development cycle.
- **Credit**: unless you prefer to remain anonymous, contributors of valid reports are credited in the advisory and the changelog.

## Scope

In scope:

- Authentication / authorization flaws (e.g., admin command bypass).
- Privacy leaks — anything that could reveal a user's identity, Telegram ID, message content, or break the anonymity guarantee.
- Injection (command, SQL, Lua) or remote code execution.
- Denial-of-service via crafted inputs.
- Dependency vulnerabilities with a practical exploit path.

Out of scope:

- Issues in Telegram's own Bot API or infrastructure.
- Reports requiring an unrealistic threat model (e.g., an attacker with full server root).
- Social engineering of individual users.

Thank you for helping keep Whisper and its users safe.
