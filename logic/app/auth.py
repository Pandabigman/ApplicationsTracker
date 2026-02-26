import os
import jwt
import httpx
from datetime import datetime, timedelta, timezone
from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

security = HTTPBearer()

# Cache the JWKS to avoid fetching on every request, refresh every hour
_jwks_cache = None
_jwks_cache_time: datetime | None = None
_JWKS_TTL = timedelta(hours=1)


async def _get_jwks():
    """Fetch Clerk's JWKS (JSON Web Key Set) for JWT verification."""
    global _jwks_cache, _jwks_cache_time
    now = datetime.now(tz=timezone.utc)
    if _jwks_cache is not None and _jwks_cache_time is not None:
        if now - _jwks_cache_time < _JWKS_TTL:
            return _jwks_cache

    clerk_secret_key = os.environ.get("CLERK_SECRET_KEY", "")
    # Extract the Clerk instance ID from the secret key to build the JWKS URL
    # Clerk secret keys look like: sk_test_xxxx or sk_live_xxxx
    # The JWKS URL uses the Clerk Frontend API domain

    clerk_jwks_url = os.environ.get("CLERK_JWKS_URL")
    if not clerk_jwks_url:
        raise HTTPException(
            status_code=500,
            detail="CLERK_JWKS_URL environment variable not configured",
        )

    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(clerk_jwks_url)
            response.raise_for_status()
            _jwks_cache = response.json()
            _jwks_cache_time = datetime.now(tz=timezone.utc)
            return _jwks_cache
        except Exception as e:
            print(f"Error fetching JWKS from {clerk_jwks_url}: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail="Authentication provider unavailable.",
            )


def _get_signing_key(jwks: dict, token: str) -> str:
    """Extract the correct signing key from JWKS based on the token's kid header."""
    unverified_header = jwt.get_unverified_header(token)
    kid = unverified_header.get("kid")

    for key in jwks.get("keys", []):
        if key.get("kid") == kid:
            return jwt.algorithms.RSAAlgorithm.from_jwk(key)

    raise HTTPException(status_code=401, detail="Unable to find signing key")


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> str:
    """FastAPI dependency that verifies Clerk JWT and returns the user ID."""
    token = credentials.credentials
    try:
        jwks = await _get_jwks()
        signing_key = _get_signing_key(jwks, token)

        payload = jwt.decode(
            token,
            signing_key,
            algorithms=["RS256"],
            options={"verify_aud": False},
        )

        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid token: no sub claim")

        return user_id

    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token.")
