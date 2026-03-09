"""
Unit tests for app/auth.py

Tests JWT verification logic, JWKS caching, signing key lookup, and error
handling — all in isolation (no network, no DB).
"""
import base64
import json
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timezone, timedelta
from fastapi import HTTPException

import app.auth as auth_module
from app.auth import _get_jwks, _get_signing_key


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _b64url(data: dict) -> str:
    """URL-safe base64 encode a dict (no padding)."""
    return base64.urlsafe_b64encode(
        json.dumps(data).encode()
    ).rstrip(b"=").decode()


def _make_fake_token(kid: str = "test-kid") -> str:
    """Build a syntactically valid JWT with a known kid (unsigned, for header parsing)."""
    header = _b64url({"alg": "RS256", "kid": kid})
    payload = _b64url({"sub": "user_abc123", "iss": "https://clerk.test"})
    return f"{header}.{payload}.AAAA"


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(autouse=True)
def reset_jwks_cache():
    """Reset module-level JWKS cache before and after every test."""
    auth_module._jwks_cache = None
    auth_module._jwks_cache_time = None
    yield
    auth_module._jwks_cache = None
    auth_module._jwks_cache_time = None


def _make_mock_httpx_client(json_response: dict):
    """Return a mock async context manager that simulates httpx.AsyncClient.get()."""
    mock_response = MagicMock()
    mock_response.json.return_value = json_response
    mock_response.raise_for_status = MagicMock()

    mock_client = AsyncMock()
    mock_client.get = AsyncMock(return_value=mock_response)
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=None)
    return mock_client


# ---------------------------------------------------------------------------
# _get_jwks: fetching
# ---------------------------------------------------------------------------

@pytest.mark.unit
@pytest.mark.asyncio
async def test_get_jwks_fetches_from_configured_url(monkeypatch):
    monkeypatch.setenv("CLERK_JWKS_URL", "https://example.clerk.dev/.well-known/jwks.json")
    expected = {"keys": [{"kid": "abc", "kty": "RSA"}]}

    with patch("app.auth.httpx.AsyncClient", return_value=_make_mock_httpx_client(expected)):
        result = await _get_jwks()

    assert result == expected


@pytest.mark.unit
@pytest.mark.asyncio
async def test_get_jwks_raises_500_when_url_not_configured(monkeypatch):
    monkeypatch.delenv("CLERK_JWKS_URL", raising=False)

    with pytest.raises(HTTPException) as exc_info:
        await _get_jwks()

    assert exc_info.value.status_code == 500
    assert "CLERK_JWKS_URL" in exc_info.value.detail


@pytest.mark.unit
@pytest.mark.asyncio
async def test_get_jwks_raises_500_on_network_failure(monkeypatch):
    monkeypatch.setenv("CLERK_JWKS_URL", "https://example.clerk.dev/.well-known/jwks.json")

    failing_client = AsyncMock()
    failing_client.get = AsyncMock(side_effect=Exception("connection refused"))
    failing_client.__aenter__ = AsyncMock(return_value=failing_client)
    failing_client.__aexit__ = AsyncMock(return_value=None)

    with patch("app.auth.httpx.AsyncClient", return_value=failing_client):
        with pytest.raises(HTTPException) as exc_info:
            await _get_jwks()

    assert exc_info.value.status_code == 500
    assert "unavailable" in exc_info.value.detail


# ---------------------------------------------------------------------------
# _get_jwks: caching
# ---------------------------------------------------------------------------

@pytest.mark.unit
@pytest.mark.asyncio
async def test_get_jwks_returns_cache_when_fresh(monkeypatch):
    monkeypatch.setenv("CLERK_JWKS_URL", "https://example.clerk.dev/.well-known/jwks.json")
    cached = {"keys": [{"kid": "cached-kid"}]}
    auth_module._jwks_cache = cached
    auth_module._jwks_cache_time = datetime.now(tz=timezone.utc)  # set just now → still fresh

    with patch("app.auth.httpx.AsyncClient") as mock_cls:
        result = await _get_jwks()

    mock_cls.assert_not_called()  # should NOT have hit the network
    assert result == cached


@pytest.mark.unit
@pytest.mark.asyncio
async def test_get_jwks_refetches_when_cache_expired(monkeypatch):
    monkeypatch.setenv("CLERK_JWKS_URL", "https://example.clerk.dev/.well-known/jwks.json")
    stale = {"keys": [{"kid": "stale-kid"}]}
    fresh = {"keys": [{"kid": "fresh-kid"}]}
    auth_module._jwks_cache = stale
    # Set cache time to 2 hours ago (TTL is 1 hour)
    auth_module._jwks_cache_time = datetime.now(tz=timezone.utc) - timedelta(hours=2)

    with patch("app.auth.httpx.AsyncClient", return_value=_make_mock_httpx_client(fresh)):
        result = await _get_jwks()

    assert result == fresh


# ---------------------------------------------------------------------------
# _get_signing_key
# ---------------------------------------------------------------------------

@pytest.mark.unit
def test_get_signing_key_raises_401_when_kid_not_in_jwks():
    token = _make_fake_token(kid="missing-kid")
    fake_jwks = {"keys": [{"kid": "other-kid", "kty": "RSA"}]}

    with pytest.raises(HTTPException) as exc_info:
        _get_signing_key(fake_jwks, token)

    assert exc_info.value.status_code == 401
    assert "signing key" in exc_info.value.detail.lower()


@pytest.mark.unit
def test_get_signing_key_calls_rsa_algorithm_for_matching_kid():
    """When the kid matches, RSAAlgorithm.from_jwk() is called with the correct key."""
    rsa_key_dict = {"kid": "test-kid", "kty": "RSA", "n": "abc", "e": "AQAB"}
    fake_jwks = {"keys": [rsa_key_dict]}
    token = _make_fake_token(kid="test-kid")

    with patch("app.auth.jwt.algorithms.RSAAlgorithm.from_jwk", return_value="mock-key") as mock_fn:
        result = _get_signing_key(fake_jwks, token)

    mock_fn.assert_called_once_with(rsa_key_dict)
    assert result == "mock-key"
