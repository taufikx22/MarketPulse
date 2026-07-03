# Clerk JWT verification middleware.
# Fetches JWKS from Clerk, caches the signing keys, and verifies Bearer tokens
# on incoming requests. Extracts user_id and org_id from the token claims.

import time
import jwt
import httpx
from fastapi import Request, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jwt import PyJWKClient
from app.config import get_settings
from dataclasses import dataclass
from typing import Optional

security = HTTPBearer(auto_error=False)

_jwks_client: Optional[PyJWKClient] = None
_jwks_client_initialized_at: float = 0


def _get_jwks_client() -> PyJWKClient:
    global _jwks_client, _jwks_client_initialized_at
    now = time.time()
    # Refresh JWKS cache every 6 hours
    if _jwks_client is None or (now - _jwks_client_initialized_at) > 21600:
        settings = get_settings()
        if not settings.clerk_jwks_url:
            raise HTTPException(status_code=500, detail="CLERK_JWKS_URL not configured")
        _jwks_client = PyJWKClient(settings.clerk_jwks_url)
        _jwks_client_initialized_at = now
    return _jwks_client


@dataclass
class ClerkUser:
    user_id: str
    org_id: Optional[str]
    org_role: Optional[str]


def verify_token(token: str) -> ClerkUser:
    client = _get_jwks_client()
    try:
        signing_key = client.get_signing_key_from_jwt(token)
        payload = jwt.decode(
            token,
            signing_key.key,
            algorithms=["RS256"],
            options={"verify_aud": False},  # Clerk tokens don't always set aud
        )
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError as e:
        raise HTTPException(status_code=401, detail=f"Invalid token: {e}")

    return ClerkUser(
        user_id=payload.get("sub", ""),
        org_id=payload.get("org_id"),
        org_role=payload.get("org_role"),
    )


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
) -> ClerkUser:
    settings = get_settings()
    if not settings.clerk_jwks_url:
        # Dev fallback when Clerk is not configured
        return ClerkUser(
            user_id="mock_user_123",
            org_id="mock_org_123",
            org_role="admin",
        )

    if credentials is None:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return verify_token(credentials.credentials)


async def require_analyst(user: ClerkUser = Depends(get_current_user)) -> ClerkUser:
    if user.org_role not in ("admin", "org:admin", "analyst", "org:analyst"):
        raise HTTPException(status_code=403, detail="Analyst role required")
    return user

