FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

COPY pyproject.toml readme.md LICENSE ./
COPY bot/ bot/
RUN pip install --no-cache-dir .

COPY alembic/ alembic/
COPY alembic.ini .

CMD ["python", "-m", "bot.main"]
