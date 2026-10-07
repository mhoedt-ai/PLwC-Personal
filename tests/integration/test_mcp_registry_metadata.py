"""Registry metadata stays unpublished until a Personal MCPB is hashed."""

from __future__ import annotations

import json
from pathlib import Path

from plwc_gateway.mcp.server_constants import (
    FORBIDDEN_PUBLIC_SERVER_NAMES,
    PUBLIC_SERVER_NAME,
)


ROOT = Path(__file__).resolve().parents[2]
SERVER_JSON = ROOT / "server.json"


def _load_server_metadata() -> dict:
    return json.loads(SERVER_JSON.read_text(encoding="utf-8"))


def test_registry_server_json_does_not_claim_an_unbuilt_personal_mcpb() -> None:
    metadata = _load_server_metadata()

    assert metadata["name"] == f"io.github.mhoedt-ai/{PUBLIC_SERVER_NAME}"
    assert metadata["version"] == "1.0.0"
    assert metadata["repository"] == {
        "url": "https://github.com/mhoedt-ai/PLwC-Personal",
        "source": "github",
    }

    assert metadata["packages"] == []


def test_registry_server_json_does_not_expose_bypass_server_names() -> None:
    metadata_text = SERVER_JSON.read_text(encoding="utf-8")

    assert PUBLIC_SERVER_NAME in metadata_text
    for forbidden_name in FORBIDDEN_PUBLIC_SERVER_NAMES:
        assert forbidden_name not in metadata_text

    metadata = _load_server_metadata()
    assert "remotes" not in metadata
    assert metadata["packages"] == []
