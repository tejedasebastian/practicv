from __future__ import annotations

import os
import socket
import subprocess
import sys
import time
from collections.abc import Generator
from pathlib import Path

import httpx
import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, text

from tests.e2e.support import ApiContext

TEST_DATABASE_URL = os.environ.get(
    "PRACTICV_TEST_DATABASE_URL",
    "postgresql+psycopg://practicv:practicv@localhost:5434/practicv_test",
)
MCP_FIXTURE_DIR = Path(__file__).resolve().parent / "mcp_fixtures"
os.environ["PRACTICV_DATABASE_URL"] = TEST_DATABASE_URL
os.environ["PRACTICV_ENVIRONMENT"] = "test"
os.environ["PRACTICV_MCP_FIXTURE_DIR"] = str(MCP_FIXTURE_DIR)

BACKEND_DIR = Path(__file__).resolve().parents[2]


def _reset_database() -> None:
    engine = create_engine(TEST_DATABASE_URL, isolation_level="AUTOCOMMIT")
    with engine.connect() as connection:
        connection.execute(text("DROP SCHEMA IF EXISTS public CASCADE"))
        connection.execute(text("CREATE SCHEMA public"))
    engine.dispose()


def _run_migrations() -> None:
    config = Config(str(BACKEND_DIR / "alembic.ini"))
    config.set_main_option("script_location", str(BACKEND_DIR / "migrations"))
    config.set_main_option("sqlalchemy.url", TEST_DATABASE_URL)
    command.upgrade(config, "head")


def _seed() -> tuple[str, list[str], list[str]]:
    from practicv.adapters.db.session import SessionLocal
    from practicv.seed import seed_demo

    with SessionLocal() as session:
        result = seed_demo(session, volume=50)
        session.commit()
    return (
        str(result.profile_id),
        [str(value) for value in result.offer_ids],
        [str(value) for value in result.application_ids],
    )


def _free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


@pytest.fixture(scope="session")
def api() -> Generator[ApiContext]:
    _reset_database()
    _run_migrations()
    profile_id, offer_ids, application_ids = _seed()

    port = _free_port()
    env = {
        **os.environ,
        "PRACTICV_DATABASE_URL": TEST_DATABASE_URL,
        "PRACTICV_ENVIRONMENT": "test",
    }
    process = subprocess.Popen(
        [
            sys.executable,
            "-m",
            "uvicorn",
            "practicv.main:app",
            "--host",
            "127.0.0.1",
            "--port",
            str(port),
            "--log-level",
            "warning",
        ],
        env=env,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        text=True,
    )
    base_url = f"http://127.0.0.1:{port}"
    try:
        deadline = time.time() + 20
        last_error: Exception | None = None
        while time.time() < deadline:
            try:
                response = httpx.get(f"{base_url}/health", timeout=1.0)
                if response.status_code == 200:
                    break
            except httpx.HTTPError as exc:
                last_error = exc
            time.sleep(0.2)
        else:
            process.terminate()
            raise AssertionError(f"API did not start: {last_error}")

        yield ApiContext(
            base_url=base_url,
            profile_id=profile_id,
            offer_ids=offer_ids,
            application_ids=application_ids,
        )
    finally:
        process.terminate()
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait(timeout=5)


@pytest.fixture(scope="session")
def client(api: ApiContext) -> Generator[httpx.Client]:
    with httpx.Client(base_url=api.base_url, timeout=10.0) as http_client:
        yield http_client
