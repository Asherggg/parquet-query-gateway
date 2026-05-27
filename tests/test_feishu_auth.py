from __future__ import annotations

import yaml
from fastapi.testclient import TestClient

from parquet_gateway.app import create_app, reset_config_cache
from parquet_gateway.auth import TokenAuthenticator
from parquet_gateway.config import load_config


class FakeFeishuOAuthClient:
    def exchange_code(self, code: str, redirect_uri: str) -> dict:
        assert code == "auth-code"
        assert redirect_uri == "http://127.0.0.1:8765/callback"
        return {
            "access_token": "feishu-user-access-token",
            "open_id": "ou_alice",
            "email": "alice@example.com",
        }


def write_feishu_config(base_config_path, target_path):
    raw = yaml.safe_load(base_config_path.read_text(encoding="utf-8"))
    raw["auth"] = {
        "gateway_token_secret": "unit-test-secret",
        "token_ttl_seconds": 3600,
        "feishu": {
            "enabled": True,
            "app_id": "cli_a_test",
            "app_secret": "secret",
            "redirect_uri": "http://127.0.0.1:8765/callback",
        },
        "feishu_users": [
            {
                "open_id": "ou_alice",
                "id": "alice",
                "roles": ["analyst"],
                "attributes": {"regions": ["US"]},
            }
        ],
    }
    target_path.write_text(yaml.safe_dump(raw), encoding="utf-8")
    return target_path


def test_loads_feishu_auth_config(sample_gateway_config, tmp_path):
    config = load_config(write_feishu_config(sample_gateway_config, tmp_path / "feishu.yml"))

    assert config.auth is not None
    assert config.auth.feishu.enabled is True
    assert config.auth.feishu_users[0].open_id == "ou_alice"


def test_exchanges_feishu_code_for_gateway_token(monkeypatch, sample_gateway_config, tmp_path):
    config_path = write_feishu_config(sample_gateway_config, tmp_path / "feishu.yml")
    monkeypatch.setenv("PARQUET_GATEWAY_CONFIG", str(config_path))
    monkeypatch.setenv("PARQUET_GATEWAY_AUDIT_DB", str(tmp_path / "audit.sqlite3"))
    reset_config_cache()
    app = create_app(feishu_client=FakeFeishuOAuthClient())
    client = TestClient(app)

    response = client.post(
        "/auth/feishu/exchange",
        json={"code": "auth-code", "redirect_uri": "http://127.0.0.1:8765/callback"},
    )

    assert response.status_code == 200, response.json()
    payload = response.json()
    assert payload["token_type"] == "bearer"
    assert payload["expires_in"] == 3600
    principal = TokenAuthenticator(load_config(config_path)).authenticate_header(f"Bearer {payload['access_token']}")
    assert principal.id == "alice"
    assert principal.attributes["regions"] == ["US"]
