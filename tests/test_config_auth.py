from __future__ import annotations

import json

import pytest
import yaml

from parquet_gateway.auth import Principal, TokenAuthenticator, b64url_decode, issue_gateway_token
from parquet_gateway.config import load_config
from parquet_gateway.errors import AuthError
from parquet_gateway.policy import list_visible_datasets


def test_authenticates_bearer_token(sample_gateway_config):
    config = load_config(sample_gateway_config)
    principal = TokenAuthenticator(config).authenticate_header("Bearer analyst-token")

    assert principal.id == "alice"
    assert principal.roles == frozenset({"analyst"})
    assert principal.attributes["regions"] == ["US", "EU"]


def test_rejects_invalid_token(sample_gateway_config):
    config = load_config(sample_gateway_config)
    authenticator = TokenAuthenticator(config)

    with pytest.raises(AuthError):
        authenticator.authenticate_header("Bearer nope")


def test_lists_visible_datasets(sample_gateway_config):
    config = load_config(sample_gateway_config)
    principal = TokenAuthenticator(config).authenticate_header("Bearer analyst-token")

    datasets = list_visible_datasets(config, principal)

    assert datasets == [{
        "id": "orders",
        "description": "Orders",
        "columns": ["amount", "order_date", "order_id", "region"],
    }]


def test_gateway_token_resolves_current_roles_from_config(sample_gateway_config, tmp_path):
    raw = yaml.safe_load(sample_gateway_config.read_text(encoding="utf-8"))
    raw["auth"] = {
        "gateway_token_secret": "unit-test-secret",
        "token_ttl_seconds": 3600,
        "feishu": {"enabled": False},
        "feishu_users": [],
    }
    config_path = tmp_path / "gateway.yml"
    config_path.write_text(yaml.safe_dump(raw), encoding="utf-8")
    config = load_config(config_path)
    token, _ = issue_gateway_token(
        config,
        Principal(id="alice", roles=frozenset({"analyst"}), attributes={"regions": ["US"]}),
    )

    raw["users"][0]["roles"] = ["analyst", "finance"]
    raw["users"][0]["attributes"] = {"regions": ["US"], "departments": ["finance"]}
    config_path.write_text(yaml.safe_dump(raw), encoding="utf-8")
    refreshed_config = load_config(config_path)

    principal = TokenAuthenticator(refreshed_config).authenticate_header(f"Bearer {token}")

    assert principal.id == "alice"
    assert principal.roles == frozenset({"analyst", "finance"})
    assert principal.attributes == {"regions": ["US"], "departments": ["finance"]}


def test_gateway_token_payload_stores_identity_not_permissions(sample_gateway_config, tmp_path):
    raw = yaml.safe_load(sample_gateway_config.read_text(encoding="utf-8"))
    raw["auth"] = {
        "gateway_token_secret": "unit-test-secret",
        "token_ttl_seconds": 3600,
        "feishu": {"enabled": True},
        "feishu_users": [
            {
                "name": "Alice Zhang",
                "id": "alice",
                "roles": ["analyst"],
                "attributes": {"regions": ["US"]},
            }
        ],
    }
    config_path = tmp_path / "gateway.yml"
    config_path.write_text(yaml.safe_dump(raw), encoding="utf-8")
    config = load_config(config_path)

    token, _ = issue_gateway_token(
        config,
        Principal(
            id="alice",
            name="Alice Zhang",
            roles=frozenset({"analyst"}),
            attributes={"regions": ["US"]},
        ),
    )
    payload = json.loads(b64url_decode(token.split(".")[1]).decode("utf-8"))

    assert payload["sub"] == "alice"
    assert payload["name"] == "Alice Zhang"
    assert "roles" not in payload
    assert "attributes" not in payload
