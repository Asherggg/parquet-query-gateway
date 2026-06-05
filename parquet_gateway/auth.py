from __future__ import annotations

from dataclasses import dataclass
import base64
import hashlib
import hmac
import json
import time
from typing import Any

from parquet_gateway.config import FeishuUserConfig, GatewayConfig, UserConfig
from parquet_gateway.errors import AuthError


@dataclass(frozen=True)
class Principal:
    id: str
    roles: frozenset[str]
    attributes: dict[str, Any]
    name: str | None = None

    @classmethod
    def from_config(cls, user: UserConfig) -> "Principal":
        return cls(id=user.id, roles=frozenset(user.roles), attributes=dict(user.attributes))

    @classmethod
    def from_feishu_config(cls, user: FeishuUserConfig) -> "Principal":
        return cls(id=user.id, roles=frozenset(user.roles), attributes=dict(user.attributes), name=user.name)


class TokenAuthenticator:
    def __init__(self, config: GatewayConfig):
        self.config = config
        self._users_by_token = {user.token: Principal.from_config(user) for user in config.users}

    def authenticate_header(self, authorization: str | None) -> Principal:
        if not authorization:
            raise AuthError("missing Authorization header")
        scheme, _, token = authorization.partition(" ")
        if scheme.lower() != "bearer" or not token:
            raise AuthError("Authorization must use Bearer token")
        principal = self._users_by_token.get(token)
        if principal is not None:
            return principal
        principal = verify_gateway_token(self.config, token)
        if principal is not None:
            return principal
        raise AuthError("invalid bearer token")


def issue_gateway_token(config: GatewayConfig, principal: Principal, now: int | None = None) -> tuple[str, int]:
    if config.auth is None:
        raise AuthError("dynamic gateway token auth is not configured")
    issued_at = int(now or time.time())
    expires_at = issued_at + config.auth.token_ttl_seconds
    payload = {
        "sub": principal.id,
        "iat": issued_at,
        "exp": expires_at,
    }
    if principal.name:
        payload["name"] = principal.name
    payload_b64 = b64url_encode(json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8"))
    signature = sign(config.auth.gateway_token_secret, payload_b64)
    return f"pgw.{payload_b64}.{signature}", config.auth.token_ttl_seconds


def verify_gateway_token(config: GatewayConfig, token: str, now: int | None = None) -> Principal | None:
    if config.auth is None or not token.startswith("pgw."):
        return None
    parts = token.split(".")
    if len(parts) != 3:
        return None
    _, payload_b64, signature = parts
    expected = sign(config.auth.gateway_token_secret, payload_b64)
    if not hmac.compare_digest(signature, expected):
        return None
    try:
        payload = json.loads(b64url_decode(payload_b64).decode("utf-8"))
    except (ValueError, json.JSONDecodeError):
        return None
    if int(payload.get("exp", 0)) < int(now or time.time()):
        return None
    return resolve_dynamic_principal(config, payload)


def resolve_dynamic_principal(config: GatewayConfig, payload: dict[str, Any]) -> Principal | None:
    name = payload.get("name")
    if name and config.auth is not None:
        for user in config.auth.feishu_users:
            if user.name == name:
                return Principal.from_feishu_config(user)

    # Backward compatibility for tokens issued before identity-only claims.
    # These tokens did not carry a Feishu name, so resolve by the stable local id
    # but still use current server-side roles and attributes.
    subject = str(payload.get("sub") or "")
    if not subject:
        return None
    for user in config.users:
        if user.id == subject:
            return Principal.from_config(user)
    if config.auth is not None:
        for user in config.auth.feishu_users:
            if user.id == subject:
                return Principal.from_feishu_config(user)
    return None


def b64url_encode(value: bytes) -> str:
    return base64.urlsafe_b64encode(value).decode("ascii").rstrip("=")


def b64url_decode(value: str) -> bytes:
    padding = "=" * (-len(value) % 4)
    return base64.urlsafe_b64decode(value + padding)


def sign(secret: str, payload_b64: str) -> str:
    digest = hmac.new(secret.encode("utf-8"), payload_b64.encode("ascii"), hashlib.sha256).digest()
    return b64url_encode(digest)
