from __future__ import annotations

import base64
import json
from functools import lru_cache
from typing import Any

import httpx
from fastapi import Depends, HTTPException, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from .env import Settings

bearer_scheme = HTTPBearer(auto_error=False)


def _decode_segment(segment: str) -> dict[str, Any]:
    padded = segment + "=" * (-len(segment) % 4)
    try:
        return json.loads(base64.urlsafe_b64decode(padded.encode("ascii")))
    except (ValueError, TypeError) as exc:
        raise HTTPException(status_code=401, detail="Invalid authentication token.") from exc


def _unverified_payload(token: str) -> dict[str, Any]:
    parts = token.split(".")
    if len(parts) != 3:
        raise HTTPException(status_code=401, detail="Invalid authentication token.")
    return _decode_segment(parts[1])


@lru_cache(maxsize=4)
def _fetch_jwks(jwks_url: str) -> dict[str, Any]:
    response = httpx.get(jwks_url, timeout=5.0)
    response.raise_for_status()
    return response.json()


def _verified_payload(token: str, settings: Settings) -> dict[str, Any]:
    if not settings.clerk_jwks_url:
        return _unverified_payload(token)

    try:
        import jwt
        from jwt import PyJWKClient
    except ModuleNotFoundError as exc:
        raise HTTPException(
            status_code=503,
            detail="JWT verification dependency is not installed.",
        ) from exc

    try:
        signing_key = PyJWKClient(settings.clerk_jwks_url).get_signing_key_from_jwt(token)
        options = {"verify_aud": False}
        return jwt.decode(
            token,
            signing_key.key,
            algorithms=["RS256"],
            issuer=settings.clerk_issuer,
            options=options,
        )
    except Exception as exc:
        raise HTTPException(status_code=401, detail="Invalid authentication token.") from exc


def get_current_user_id(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
) -> str:
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise HTTPException(status_code=401, detail="Authentication required.")

    settings: Settings = request.app.state.settings
    payload = _verified_payload(credentials.credentials, settings)

    if settings.clerk_issuer and payload.get("iss") != settings.clerk_issuer:
        raise HTTPException(status_code=401, detail="Invalid token issuer.")

    user_id = payload.get("sub")
    if not isinstance(user_id, str) or not user_id.strip():
        raise HTTPException(status_code=401, detail="Token is missing a user subject.")

    request.state.user_id = user_id
    return user_id
