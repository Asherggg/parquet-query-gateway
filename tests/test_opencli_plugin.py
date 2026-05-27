from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_opencli_plugin_manifest_exists():
    manifest = json.loads((ROOT / "opencli-plugin.json").read_text(encoding="utf-8"))

    assert manifest["name"] == "parquet"
    assert manifest["opencli"] == ">=1.0.0"


def test_opencli_plugin_commands_register_parquet_site():
    for filename in ["datasets.js", "schema.js", "query.js", "audit.js", "login.js"]:
        source = (ROOT / filename).read_text(encoding="utf-8")
        assert "from '@jackwener/opencli/registry'" in source
        assert "site: 'parquet'" in source
        assert "browser: false" in source


def test_opencli_plugin_login_uses_feishu_exchange():
    source = (ROOT / "login.js").read_text(encoding="utf-8")

    assert "/auth/feishu/exchange" in source
    assert "PARQUET_GATEWAY_TOKEN" in source


def test_opencli_plugin_login_is_one_click_flow():
    source = (ROOT / "login.js").read_text(encoding="utf-8")

    assert "createServer" in source
    assert "openBrowser" in source
    assert "waitForCallbackCode" in source
    assert "saveGatewayToken" in source
    assert "PARQUET_FEISHU_AUTH_URL" in source
    assert "http://127.0.0.1:8765/callback" in source


def test_opencli_plugin_query_uses_gateway_not_local_files():
    source = (ROOT / "query.js").read_text(encoding="utf-8")
    client_source = (ROOT / "gateway-client.js").read_text(encoding="utf-8")

    assert "PARQUET_GATEWAY_URL" in client_source
    assert "PARQUET_GATEWAY_TOKEN" in client_source
    assert "read_parquet" not in source
    assert "/query" in source
