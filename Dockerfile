# Used when Railway builds from the monorepo root (GitHub deploy).
FROM python:3.13-slim

WORKDIR /app

RUN pip install --no-cache-dir uv

COPY apps/api/pyproject.toml apps/api/uv.lock ./
COPY apps/api/app ./app
COPY apps/api/alembic ./alembic
COPY apps/api/alembic.ini ./

RUN uv sync --no-dev --frozen

ENV PATH="/app/.venv/bin:$PATH"
EXPOSE 8000

CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
