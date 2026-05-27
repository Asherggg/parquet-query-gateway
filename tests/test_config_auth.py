from __future__ import annotations

import pytest

from parquet_gateway.auth import TokenAuthenticator
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
