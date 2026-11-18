from __future__ import annotations

import json
import sys
from pathlib import Path

from practicv.config import get_settings
from practicv.domain.errors import MCPUnavailableError, ValidationError


def _default_server_path() -> Path:
    return Path(__file__).resolve().parents[6] / "mcp" / "practicas_pe_server.py"


def _tool_payload(result: object) -> dict:
    content = getattr(result, "content", [])
    for item in content:
        text = getattr(item, "text", None)
        if text:
            try:
                return json.loads(text)
            except json.JSONDecodeError as exc:
                raise MCPUnavailableError("MCP returned invalid JSON.") from exc
    raise MCPUnavailableError("MCP returned an empty response.")


class PracticasPeMCPClient:
    def __init__(self, server_path: str | None = None) -> None:
        self.server_path = Path(server_path) if server_path else _default_server_path()

    async def _call(self, tool: str, arguments: dict) -> dict:
        if not self.server_path.exists():
            raise MCPUnavailableError(
                "MCP practicas-pe is not available. Use manual, CSV, or URL capture.",
                {"server_path": str(self.server_path)},
            )
        try:
            from mcp import ClientSession, StdioServerParameters
            from mcp.client.stdio import stdio_client

            params = StdioServerParameters(
                command=sys.executable,
                args=[str(self.server_path)],
            )
            async with (
                stdio_client(params) as (read, write),
                ClientSession(read, write) as session,
            ):
                await session.initialize()
                result = await session.call_tool(tool, arguments)
                payload = _tool_payload(result)
        except MCPUnavailableError:
            raise
        except Exception as exc:
            raise MCPUnavailableError(
                "MCP practicas-pe failed. Use manual, CSV, or URL capture.",
                {"tool": tool, "error": str(exc)},
            ) from exc
        if "error" in payload:
            raise MCPUnavailableError(
                "MCP practicas-pe returned an error.",
                {"tool": tool, "error": payload["error"]},
            )
        return payload

    async def list_filters(self) -> dict:
        return await self._call("listar_filtros", {})

    async def search(
        self,
        q: str = "",
        modality: str = "preprofesional",
        career: str | None = None,
        department: str | None = None,
        order: str = "recientes",
        page: int = 1,
        pages: int = 1,
        limit: int = 30,
    ) -> dict:
        arguments = {
            "q": q,
            "modalidad": modality,
            "orden": order,
            "pagina": page,
            "paginas": pages,
            "limite": limit,
        }
        if career:
            arguments["carrera"] = career
        if department:
            arguments["departamento"] = department
        return await self._call("buscar_practicas", arguments)

    async def get_offer(self, url: str) -> dict:
        return await self._call("obtener_practica", {"url": url})


class FixtureMCPClient:
    def __init__(self, fixture_dir: str) -> None:
        self.fixture_dir = Path(fixture_dir)

    def _read(self, filename: str) -> dict:
        path = self.fixture_dir / filename
        if not path.exists():
            raise MCPUnavailableError(
                "MCP fixture is not available. Use manual, CSV, or URL capture.",
                {"fixture": filename},
            )
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise MCPUnavailableError(
                "MCP fixture could not be read.",
                {"fixture": filename},
            ) from exc

    async def list_filters(self) -> dict:
        return self._read("filters.json")

    async def search(
        self,
        q: str = "",
        modality: str = "preprofesional",
        career: str | None = None,
        department: str | None = None,
        order: str = "recientes",
        page: int = 1,
        pages: int = 1,
        limit: int = 30,
    ) -> dict:
        return self._read("search.json")

    async def get_offer(self, url: str) -> dict:
        payload = self._read("offer.json")
        offers = payload.get("offers", payload if isinstance(payload, list) else [])
        for offer in offers:
            if offer.get("url") == url:
                return offer
        raise ValidationError("Offer not found in MCP fixture.", {"url": url})


class DisabledMCPClient:
    async def list_filters(self) -> dict:
        raise MCPUnavailableError("MCP practicas-pe is disabled.")

    async def search(self, **kwargs: object) -> dict:
        raise MCPUnavailableError("MCP practicas-pe is disabled.")

    async def get_offer(self, url: str) -> dict:
        raise MCPUnavailableError("MCP practicas-pe is disabled.", {"url": url})


MCPClient = PracticasPeMCPClient | FixtureMCPClient | DisabledMCPClient


def get_mcp_client() -> MCPClient:
    settings = get_settings()
    if not settings.mcp_enabled:
        return DisabledMCPClient()
    if settings.mcp_fixture_dir:
        return FixtureMCPClient(settings.mcp_fixture_dir)
    return PracticasPeMCPClient(settings.mcp_server_path)
