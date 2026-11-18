FROM python:3.13-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

COPY pyproject.toml ./
COPY practicv ./practicv
COPY alembic.ini ./
COPY migrations ./migrations
COPY docker-entrypoint.sh ./

RUN pip install --no-cache-dir . \
    && chmod +x docker-entrypoint.sh

EXPOSE 8000

ENTRYPOINT ["./docker-entrypoint.sh"]
