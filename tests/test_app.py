from __future__ import annotations

from fastapi.testclient import TestClient

from parquet_gateway.app import create_app, reset_config_cache


def make_client(monkeypatch, sample_gateway_config, tmp_path):
    monkeypatch.setenv("PARQUET_GATEWAY_CONFIG", str(sample_gateway_config))
    monkeypatch.setenv("PARQUET_GATEWAY_AUDIT_DB", str(tmp_path / "audit.sqlite3"))
    reset_config_cache()
    return TestClient(create_app())


def test_health(monkeypatch, sample_gateway_config, tmp_path):
    client = make_client(monkeypatch, sample_gateway_config, tmp_path)

    response = client.get("/health")

    assert response.status_code == 200, response.json()
    assert response.json() == {"status": "ok"}


def test_datasets_requires_auth(monkeypatch, sample_gateway_config, tmp_path):
    client = make_client(monkeypatch, sample_gateway_config, tmp_path)

    response = client.get("/datasets")

    assert response.status_code == 401


def test_query_applies_permissions_and_audits(monkeypatch, sample_gateway_config, tmp_path):
    client = make_client(monkeypatch, sample_gateway_config, tmp_path)

    response = client.post(
        "/query",
        headers={"Authorization": "Bearer analyst-token"},
        json={
            "dataset": "orders",
            "select": ["order_id", "region"],
            "order_by": [{"field": "order_id", "direction": "asc"}],
            "limit": 10,
        },
    )

    assert response.status_code == 200, response.json()
    payload = response.json()
    assert payload["row_count"] == 2
    assert payload["rows"] == [
        {"order_id": 1, "region": "US"},
        {"order_id": 2, "region": "EU"},
    ]
    assert client.app.state.audit.recent()[0]["allowed"] is True


def test_query_denies_hidden_column_and_audits(monkeypatch, sample_gateway_config, tmp_path):
    client = make_client(monkeypatch, sample_gateway_config, tmp_path)

    response = client.post(
        "/query",
        headers={"Authorization": "Bearer analyst-token"},
        json={"dataset": "orders", "select": ["customer_email"]},
    )

    assert response.status_code == 403
    assert response.json()["error"]["code"] == "permission_denied"
    assert client.app.state.audit.recent()[0]["allowed"] is False


def test_admin_can_read_audit_events(monkeypatch, sample_gateway_config, tmp_path):
    client = make_client(monkeypatch, sample_gateway_config, tmp_path)
    client.post(
        "/query",
        headers={"Authorization": "Bearer analyst-token"},
        json={"dataset": "orders", "select": ["order_id"], "limit": 1},
    )

    response = client.get("/admin/audit", headers={"Authorization": "Bearer admin-token"})

    assert response.status_code == 200, response.json()
    payload = response.json()
    assert payload["events"][0]["user_id"] == "alice"
    assert payload["events"][0]["dataset"] == "orders"


def test_non_admin_cannot_read_audit_events(monkeypatch, sample_gateway_config, tmp_path):
    client = make_client(monkeypatch, sample_gateway_config, tmp_path)

    response = client.get("/admin/audit", headers={"Authorization": "Bearer analyst-token"})

    assert response.status_code == 403
