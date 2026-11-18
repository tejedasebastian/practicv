#!/bin/sh
set -eu

alembic upgrade head

exec uvicorn practicv.main:app --host 0.0.0.0 --port 8000
