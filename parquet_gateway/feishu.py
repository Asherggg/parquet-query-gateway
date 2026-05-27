from __future__ import annotations

from typing import Protocol

from pydantic import BaseModel

from parquet_gateway.auth import Principal, issue_gateway_token
from parquet_gateway.config import FeishuUserConfig, GatewayConfig
from parquet_gateway.errors import AuthError, PermissionDenied


class FeishuExchangeRequest(BaseModel):
    code: str
    redirect_uri: str


class FeishuOAuthClientProtocol(Protocol):
    def exchange_code(self, code: str, redirect_uri: str) -> dict:
        ...


class FeishuOAuthClient:
    def __init__(self, config: GatewayConfig):
        self.config = config

    def exchange_code(self, code: str, redirect_uri: str) -> dict:
        # The concrete Feishu HTTP exchange is intentionally isolated here so
        # tests can inject a fake client and secrets never move into OpenCLI.
        import urllib.request
        import json

        if self.config.auth is None:
            raise AuthError("feishu auth is not configured")
        feishu = self.config.auth.feishu
        payload = json.dumps({
            "grant_type": "authorization_code",
            "client_id": feishu.app_id,
            "client_secret": feishu.app_secret,
            "code": code,
            "redirect_uri": redirect_uri,
        }).encode("utf-8")
        req = urllib.request.Request(
            "https://open.feishu.cn/open-apis/authen/v2/oauth/token",
            data=payload,
            method="POST",
            headers={"Content-Type": "application/json", "Accept": "application/json"},
        )
        with urllib.request.urlopen(req, timeout=20) as response:
            raw = json.loads(response.read().decode("utf-8"))
        if raw.get("code", 0) != 0:
            raise AuthError(f"feishu token exchange failed: {raw.get('msg', 'unknown error')}")
        data = raw.get("data", {})
        return {
            "access_token": data.get("access_token"),
            "open_id": data.get("open_id"),
            "email": data.get("email"),
        }


def exchange_feishu_code_for_gateway_token(
    config: GatewayConfig,
    client: FeishuOAuthClientProtocol,
    request: FeishuExchangeRequest,
) -> dict:
    if config.auth is None or not config.auth.feishu.enabled:
        raise AuthError("feishu auth is not enabled")
    if request.redirect_uri != config.auth.feishu.redirect_uri:
        raise AuthError("redirect_uri does not match configured feishu redirect_uri")

    profile = client.exchange_code(request.code, request.redirect_uri)
    user = resolve_feishu_user(config.auth.feishu_users, profile)
    principal = Principal.from_feishu_config(user)
    token, ttl = issue_gateway_token(config, principal)
    return {
        "access_token": token,
        "token_type": "bearer",
        "expires_in": ttl,
        "user": {
            "id": principal.id,
            "roles": sorted(principal.roles),
        },
    }


def resolve_feishu_user(users: list[FeishuUserConfig], profile: dict) -> FeishuUserConfig:
    open_id = profile.get("open_id")
    email = profile.get("email")
    for user in users:
        if user.open_id and user.open_id == open_id:
            return user
        if user.email and user.email == email:
            return user
    raise PermissionDenied("feishu user is not mapped to gateway permissions")
