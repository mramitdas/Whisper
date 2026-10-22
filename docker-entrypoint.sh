#!/bin/sh
# Container entrypoint: bring the schema up to date, then hand off to the bot.
set -e

echo "==> Applying database migrations"
alembic upgrade head

echo "==> Starting bot"
exec "$@"
