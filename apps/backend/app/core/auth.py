from dataclasses import dataclass
from functools import lru_cache
from typing import Annotated, Any
from uuid import UUID

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jwt import PyJWKClient
from sqlalchemy import select

from app.core.config import get_settings
from app.db.models.user import User
from app.db.session import SessionLocal

settings = get_settings()
bearer = HTTPBearer(auto_error=False)


@dataclass(frozen=True)
class CurrentUser:
    id: UUID
    subject: str
    username: str
    email: str
    display_name: str | None
    roles: frozenset[str]


@lru_cache
def get_jwks_client() -> PyJWKClient:
    return PyJWKClient(settings.keycloak_jwks_url, cache_keys=True)


def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer)],
) -> CurrentUser:
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
        )

    try:
        signing_key = get_jwks_client().get_signing_key_from_jwt(credentials.credentials)
        claims = jwt.decode(
            credentials.credentials,
            signing_key.key,
            algorithms=["RS256"],
            audience=settings.keycloak_audience,
            issuer=settings.keycloak_issuer,
        )
    except jwt.PyJWTError as error:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid access token",
        ) from error

    return _synchronize_user(claims)


def require_role(role: str):
    def dependency(user: Annotated[CurrentUser, Depends(get_current_user)]) -> CurrentUser:
        if role not in user.roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions",
            )
        return user

    return dependency


AdminUser = Annotated[CurrentUser, Depends(require_role("admin"))]
AuthenticatedUser = Annotated[CurrentUser, Depends(get_current_user)]


def _synchronize_user(claims: dict[str, Any]) -> CurrentUser:
    subject = str(claims.get("sub", ""))
    email = str(claims.get("email", "")).lower()
    username = str(claims.get("preferred_username") or email)
    display_name = claims.get("name")
    realm_access = claims.get("realm_access") or {}
    roles = frozenset(str(role) for role in realm_access.get("roles", []))

    if not subject or not email:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token is missing required identity claims",
        )

    locale = str(claims.get("locale", "en"))
    preferred_language = "de" if locale.lower().startswith("de") else "en"

    with SessionLocal() as session:
        user = session.scalar(select(User).where(User.keycloak_subject == subject))
        if user is None:
            user = session.scalar(select(User).where(User.email == email))

        if user is None:
            user = User(
                keycloak_subject=subject,
                email=email,
                display_name=display_name or username,
                preferred_language=preferred_language,
            )
            session.add(user)
        else:
            user.keycloak_subject = subject
            user.email = email
            user.display_name = display_name or username
            user.preferred_language = preferred_language

        session.commit()

        return CurrentUser(
            id=user.id,
            subject=subject,
            username=username,
            email=email,
            display_name=user.display_name,
            roles=roles,
        )
