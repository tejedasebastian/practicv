from __future__ import annotations

import os
import socket
import subprocess
import sys
import time

import httpx


def _free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


def _wait_for_health(url: str, timeout: float = 20.0) -> httpx.Response:
    deadline = time.time() + timeout
    last_error: Exception | None = None
    while time.time() < deadline:
        try:
            response = httpx.get(url, timeout=1.0)
            if response.status_code == 200:
                return response
        except httpx.HTTPError as exc:
            last_error = exc
        time.sleep(0.2)
    raise AssertionError(f"API did not become healthy: {last_error}")


def test_health_endpoint_over_http() -> None:
    port = _free_port()
    env = {**os.environ, "PRACTICV_ENVIRONMENT": "test"}
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
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )
    try:
        response = _wait_for_health(f"http://127.0.0.1:{port}/health")
        payload = response.json()
        assert payload["status"] == "ok"
        assert payload["service"] == "PractiCV"
        assert payload["version"] == "0.1.0"
        assert payload["environment"] == "test"

        root = httpx.get(f"http://127.0.0.1:{port}/", timeout=5.0)
        assert root.status_code == 200
        assert root.json()["service"] == "PractiCV"
        assert root.json()["health"] == "/health"
    except AssertionError as exc:
        process.terminate()
        try:
            output, _ = process.communicate(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()
            output, _ = process.communicate()
        raise AssertionError(f"{exc}\nServer output:\n{output}") from None
    finally:
        process.terminate()
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait(timeout=5)
