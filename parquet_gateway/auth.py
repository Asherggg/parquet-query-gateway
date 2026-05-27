from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from parquet_gateway.config import GatewayConfig, UserConfig
from parquet_gateway.errors import AuthError


@dataclass(frozen=True)
class Principal:
    id: str
    roles: frozenset[str]
    attributes: dict[str, Any]

    @classmethod
    def from_config(cls, user: UserConfig) -> "Principal":
        return cls(id=user.id, roles=frozenset(user.roles), attributes=dict(user.attributes))


class TokenAuthenticator:
    def __init__(self, config: GatewayConfig):
        self._users_by_token = {user.token: Principal.from_config(user) for user in config.users}

    def authenticate_header(self, authorization: str | None) -> Principal:
        if not authorization:
            raise AuthError("missing Authorization header")
        scheme, _, token = authorization.partition(" ")
        if scheme.lower() != "bearer" or not token:
            raise AuthError("Authorization must use Bearer token")
        principal = self._users_by_token.get(token)
        if principal is None:
            raise AuthError("invalid bearer token")
        return principal
