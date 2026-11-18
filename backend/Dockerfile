FROM python:3.13-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

COPY pyproject.toml ./
COPY practicv ./practicv

RUN pip install --no-cache-dir .

EXPOSE 8000

CMD ["uvicorn", "practicv.main:app", "--host", "0.0.0.0", "--port", "8000"]
