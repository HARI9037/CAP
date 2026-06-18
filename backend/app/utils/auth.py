from __future__ import annotations

from typing import Any
from fastapi import Depends, HTTPException, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from .env import Settings

bearer_scheme = HTTPBearer(auto_error=False)


def _verified_payload(token: str, settings: Settings) -> dict[str, Any]:
    if not settings.clerk_jwks_url or not settings.clerk_issuer:
        raise HTTPException(
            status_code=503,
            detail="Clerk JWT verification is not configured.",
        )

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

    if payload.get("iss") != settings.clerk_issuer:
        raise HTTPException(status_code=401, detail="Invalid token issuer.")

    user_id = payload.get("sub")
    if not isinstance(user_id, str) or not user_id.strip():
        raise HTTPException(status_code=401, detail="Token is missing a user subject.")

    request.state.user_id = user_id
    return user_id
