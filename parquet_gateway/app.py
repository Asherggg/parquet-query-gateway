from __future__ import annotations

import os
import time
from functools import lru_cache
from pathlib import Path

from fastapi import Depends, FastAPI, Header
from fastapi.responses import JSONResponse
from pydantic import ValidationError

from parquet_gateway.audit import AuditEvent, AuditLog
from parquet_gateway.auth import Principal, TokenAuthenticator
from parquet_gateway.config import GatewayConfig, load_config
from parquet_gateway.errors import GatewayError
from parquet_gateway.errors import PermissionDenied
from parquet_gateway.executor import DuckDBExecutor
from parquet_gateway.feishu import FeishuExchangeRequest, FeishuOAuthClient, exchange_feishu_code_for_gateway_token
from parquet_gateway.models import QueryRequest, QueryResponse
from parquet_gateway.policy import list_visible_datasets, resolve_dataset_access
from parquet_gateway.query_builder import compile_query


def create_app(feishu_client=None) -> FastAPI:
    config = get_config()
    authenticator = TokenAuthenticator(config)
    audit = AuditLog(os.environ.get("PARQUET_GATEWAY_AUDIT_DB", "audit.sqlite3"))
    executor = DuckDBExecutor(config)
    actual_feishu_client = feishu_client or FeishuOAuthClient(config)

    app = FastAPI(title="Parquet Query Gateway", version="0.1.0")

    def current_principal(authorization: str | None = Header(default=None)) -> Principal:
        return authenticator.authenticate_header(authorization)

    @app.exception_handler(GatewayError)
    async def gateway_error_handler(_, exc: GatewayError) -> JSONResponse:
        return JSONResponse(status_code=exc.status_code, content={"error": {"code": exc.code, "message": exc.message}})

    @app.exception_handler(ValidationError)
    async def validation_error_handler(_, exc: ValidationError) -> JSONResponse:
        return JSONResponse(status_code=400, content={"error": {"code": "validation_error", "message": str(exc)}})

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.get("/datasets")
    def datasets(principal: Principal = Depends(current_principal)) -> dict[str, object]:
        return {"datasets": list_visible_datasets(config, principal)}

    @app.get("/datasets/{dataset_id}/schema")
    def schema(dataset_id: str, principal: Principal = Depends(current_principal)) -> dict[str, object]:
        access = resolve_dataset_access(config, principal, dataset_id)
        return {
            "dataset": dataset_id,
            "description": access.dataset.description,
            "columns": sorted(access.allowed_columns),
        }

    @app.post("/query", response_model=QueryResponse)
    def query(request: QueryRequest, principal: Principal = Depends(current_principal)) -> QueryResponse:
        start = time.perf_counter()
        try:
            compiled = compile_query(config, principal, request)
            response = executor.execute(compiled)
            audit.record(AuditEvent(
                user_id=principal.id,
                dataset=request.dataset,
                action="query",
                allowed=True,
                details={
                    "columns": response.columns,
                    "filters": [filter_.model_dump() for filter_ in request.filters],
                },
                row_count=response.row_count,
                duration_ms=response.query_ms,
            ))
            return response
        except GatewayError as exc:
            audit.record(AuditEvent(
                user_id=principal.id,
                dataset=request.dataset,
                action="query",
                allowed=False,
                reason=exc.message,
                duration_ms=int((time.perf_counter() - start) * 1000),
            ))
            raise

    @app.get("/admin/audit")
    def audit_events(
        principal: Principal = Depends(current_principal),
        limit: int = 100,
    ) -> dict[str, object]:
        if "admin" not in principal.roles:
            raise PermissionDenied("admin role is required to read audit events")
        bounded_limit = min(max(limit, 1), 1000)
        return {"events": audit.recent(bounded_limit)}

    @app.post("/auth/feishu/exchange")
    def feishu_exchange(request: FeishuExchangeRequest) -> dict[str, object]:
        return exchange_feishu_code_for_gateway_token(config, actual_feishu_client, request)

    app.state.config = config
    app.state.audit = audit
    return app


@lru_cache(maxsize=1)
def get_config() -> GatewayConfig:
    path = os.environ.get("PARQUET_GATEWAY_CONFIG", "config/example.yml")
    return load_config(Path(path))


def reset_config_cache() -> None:
    get_config.cache_clear()
