from __future__ import annotations

import logging
from typing import Any
from fastapi import Depends, HTTPException, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from .env import Settings

bearer_scheme = HTTPBearer(auto_error=False)
logger = logging.getLogger(__name__)


def _verified_payload(token: str, settings: Settings) -> dict[str, Any]:
    logger.info("Configured Clerk Issuer: %s", settings.clerk_issuer)
    logger.info("Configured Clerk JWKS URL: %s", settings.clerk_jwks_url)

    try:
        import jwt
        from jwt import PyJWKClient
        from jwt.exceptions import (
            ExpiredSignatureError,
            InvalidIssuerError,
            InvalidSignatureError,
            InvalidTokenError,
            PyJWKClientError,
        )
    except ModuleNotFoundError as exc:
        raise HTTPException(
            status_code=503,
            detail="JWT verification dependency is not installed.",
        ) from exc

    try:
        unverified_header = jwt.get_unverified_header(token)
        logger.info(
            "JWT header (unverified): alg=%s kid=%s typ=%s",
            unverified_header.get("alg"),
            unverified_header.get("kid"),
            unverified_header.get("typ"),
        )
    except Exception as exc:
        logger.exception(
            "Failed to read JWT header (unverified): %s: %s",
            exc.__class__.__name__,
            exc,
        )

    try:
        unverified_claims = jwt.decode(
            token,
            options={
                "verify_signature": False,
                "verify_exp": False,
                "verify_aud": False,
                "verify_iss": False,
            },
        )
        logger.info(
            "JWT claims (unverified): iss=%s sub=%s aud=%s exp=%s",
            unverified_claims.get("iss"),
            unverified_claims.get("sub"),
            unverified_claims.get("aud"),
            unverified_claims.get("exp"),
        )
    except Exception as exc:
        logger.exception(
            "Failed to read JWT claims (unverified): %s: %s",
            exc.__class__.__name__,
            exc,
        )

    if not settings.clerk_jwks_url or not settings.clerk_issuer:
        raise HTTPException(
            status_code=503,
            detail="Clerk JWT verification is not configured.",
        )

    try:
        logger.info("Fetching JWKS from %s", settings.clerk_jwks_url)
        signing_key = PyJWKClient(
            settings.clerk_jwks_url).get_signing_key_from_jwt(token)
        logger.info(
            "Resolved JWKS signing key: key_id=%s",
            getattr(signing_key, "key_id", None),
        )
        options = {"verify_aud": False}
        return jwt.decode(
            token,
            signing_key.key,
            algorithms=["RS256"],
            issuer=settings.clerk_issuer,
            options=options,
        )
    except Exception as exc:
        logger.exception(
            "JWT verification failed: exc_type=%s exc_message=%s invalid_signature=%s invalid_issuer=%s expired_signature=%s pyjwkclient_error=%s invalid_token=%s",
            exc.__class__.__name__,
            exc,
            isinstance(exc, InvalidSignatureError),
            isinstance(exc, InvalidIssuerError),
            isinstance(exc, ExpiredSignatureError),
            isinstance(exc, PyJWKClientError),
            isinstance(exc, InvalidTokenError),
        )
        raise HTTPException(
            status_code=401, detail="Invalid authentication token.") from exc


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
        raise HTTPException(
            status_code=401, detail="Token is missing a user subject.")

    request.state.user_id = user_id
    return user_id
