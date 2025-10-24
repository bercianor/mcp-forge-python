"""Tests for JWT validation middleware."""

import time
from unittest.mock import AsyncMock, MagicMock, patch

import jwt
import pytest
from fastapi import HTTPException

from mcp_app.middlewares.jwt_validation import JWKSCache, JWTValidationMiddleware

HTTP_401_UNAUTHORIZED = 401
CACHE_INTERVAL_DEFAULT = 600


def test_jwks_cache_init() -> None:
    """Test JWKSCache initialization."""
    cache = JWKSCache("https://example.com/jwks", CACHE_INTERVAL_DEFAULT)
    assert cache.uri == "https://example.com/jwks"
    assert cache.cache_interval == CACHE_INTERVAL_DEFAULT
    assert cache.keys == {}
    assert cache.last_updated == 0


@patch("mcp_app.middlewares.jwt_validation.requests.get")
def test_jwks_cache_refresh_keys_success(mock_get: MagicMock) -> None:
    """Test JWKSCache _refresh_keys success."""
    mock_response = MagicMock()
    mock_response.json.return_value = {"keys": [{"kid": "key1", "kty": "RSA"}]}
    mock_get.return_value = mock_response

    cache = JWKSCache("https://example.com/jwks")
    cache._refresh_keys()

    assert cache.keys == {"key1": {"kid": "key1", "kty": "RSA"}}
    assert cache.last_updated > 0


@patch("mcp_app.middlewares.jwt_validation.requests.get")
def test_jwks_cache_refresh_keys_failure(mock_get: MagicMock) -> None:
    """Test JWKSCache _refresh_keys failure."""
    mock_get.side_effect = Exception("Network error")

    cache = JWKSCache("https://example.com/jwks")
    cache._refresh_keys()

    assert cache.keys == {}
    assert cache.last_updated == 0


def test_jwks_cache_get_key_no_refresh() -> None:
    """Test JWKSCache get_key without refresh."""
    cache = JWKSCache("https://example.com/jwks")
    cache.keys = {"key1": {"kid": "key1"}}
    cache.last_updated = time.time()

    key = cache.get_key("key1")
    assert key == {"kid": "key1"}


@patch.object(JWKSCache, "_refresh_keys")
def test_jwks_cache_get_key_with_refresh(mock_refresh: MagicMock) -> None:
    """Test JWKSCache get_key with refresh."""
    cache = JWKSCache("https://example.com/jwks", 0)  # Short interval
    cache.last_updated = 0

    key = cache.get_key("key1")
    mock_refresh.assert_called_once()
    assert key is None


def test_jwt_validation_middleware_init_external() -> None:
    """Test JWTValidationMiddleware init with external strategy."""
    middleware = JWTValidationMiddleware(MagicMock(), strategy="external")
    assert middleware.strategy == "external"
    assert middleware.jwks is None


def test_jwt_validation_middleware_init_local() -> None:
    """Test JWTValidationMiddleware init with local strategy."""
    middleware = JWTValidationMiddleware(
        MagicMock(), strategy="local", jwks_uri="https://example.com/jwks"
    )
    assert middleware.strategy == "local"
    assert middleware.jwks is not None
    assert middleware.jwks.uri == "https://example.com/jwks"


@pytest.mark.asyncio
async def test_dispatch_external_strategy() -> None:
    """Test dispatch with external strategy."""
    middleware = JWTValidationMiddleware(MagicMock(), strategy="external")
    request = MagicMock()
    call_next = AsyncMock(return_value=MagicMock())

    response = await middleware.dispatch(request, call_next)
    call_next.assert_called_once_with(request)
    assert response is not None


@pytest.mark.asyncio
@patch("mcp_app.middlewares.jwt_validation.jwt.get_unverified_header")
async def test_dispatch_local_strategy(mock_get_header: MagicMock) -> None:
    """Test dispatch with local strategy."""
    mock_get_header.return_value = {"kid": "key1"}

    middleware = JWTValidationMiddleware(
        MagicMock(), strategy="local", jwks_uri="https://example.com/jwks"
    )
    assert middleware.jwks is not None
    middleware.jwks.keys = {"key1": {"kid": "key1"}}

    request = MagicMock()
    request.headers.get.return_value = "Bearer token"
    request.headers.__dict__["_list"] = []

    call_next = AsyncMock(return_value=MagicMock())

    with (
        patch("mcp_app.middlewares.jwt_validation.jwt.PyJWK") as mock_pyjwk,
        patch("mcp_app.middlewares.jwt_validation.jwt.decode") as mock_decode,
    ):
        mock_key = MagicMock()
        mock_pyjwk.return_value.key = mock_key
        mock_decode.return_value = {"user": "test"}

        response = await middleware.dispatch(request, call_next)
        call_next.assert_called_once_with(request)
        assert response is not None


@pytest.mark.asyncio
@patch("mcp_app.middlewares.jwt_validation.jwt.get_unverified_header")
async def test_validate_local_no_jwks(mock_get_header: MagicMock) -> None:
    """Test _validate_local with no JWKS configured."""
    mock_get_header.return_value = {"kid": "key1"}

    middleware = JWTValidationMiddleware(MagicMock(), strategy="local")  # No jwks_uri
    request = MagicMock()
    request.headers.get.return_value = "Bearer token"

    with pytest.raises(HTTPException) as exc_info:
        await middleware._validate_local(request)
    assert exc_info.value.status_code == HTTP_401_UNAUTHORIZED
    assert "JWKS not configured" in str(exc_info.value.detail)


@pytest.mark.asyncio
@patch("mcp_app.middlewares.jwt_validation.jwt.get_unverified_header")
async def test_validate_local_key_not_found(mock_get_header: MagicMock) -> None:
    """Test _validate_local with key not found."""
    mock_get_header.return_value = {"kid": "key1"}

    middleware = JWTValidationMiddleware(
        MagicMock(), strategy="local", jwks_uri="https://example.com/jwks"
    )
    assert middleware.jwks is not None
    middleware.jwks.keys = {}  # No key

    request = MagicMock()
    request.headers.get.return_value = "Bearer token"

    with pytest.raises(HTTPException) as exc_info:
        await middleware._validate_local(request)
    assert exc_info.value.status_code == HTTP_401_UNAUTHORIZED
    assert "Key not found in JWKS" in str(exc_info.value.detail)


@pytest.mark.asyncio
@patch("mcp_app.middlewares.jwt_validation.jwt.get_unverified_header")
@patch("mcp_app.middlewares.jwt_validation.jwt.PyJWK")
async def test_validate_local_invalid_jwk(
    mock_pyjwk: MagicMock, mock_get_header: MagicMock
) -> None:
    """Test _validate_local with invalid JWK."""
    mock_get_header.return_value = {"kid": "key1"}
    mock_pyjwk.side_effect = Exception("Invalid JWK")

    middleware = JWTValidationMiddleware(
        MagicMock(), strategy="local", jwks_uri="https://example.com/jwks"
    )
    assert middleware.jwks is not None
    middleware.jwks.keys = {"key1": {"kid": "key1"}}

    request = MagicMock()
    request.headers.get.return_value = "Bearer token"

    with pytest.raises(HTTPException) as exc_info:
        await middleware._validate_local(request)
    assert exc_info.value.status_code == HTTP_401_UNAUTHORIZED
    assert "Invalid JWK" in str(exc_info.value.detail)


@pytest.mark.asyncio
@patch("mcp_app.middlewares.jwt_validation.jwt.get_unverified_header")
@patch("mcp_app.middlewares.jwt_validation.jwt.PyJWK")
@patch("mcp_app.middlewares.jwt_validation.jwt.decode")
async def test_validate_local_expired_token(
    mock_decode: MagicMock, mock_pyjwk: MagicMock, mock_get_header: MagicMock
) -> None:
    """Test _validate_local with expired token."""
    mock_get_header.return_value = {"kid": "key1"}
    mock_key = MagicMock()
    mock_pyjwk.return_value.key = mock_key
    mock_decode.side_effect = jwt.ExpiredSignatureError("Token expired")

    middleware = JWTValidationMiddleware(
        MagicMock(), strategy="local", jwks_uri="https://example.com/jwks"
    )
    assert middleware.jwks is not None
    middleware.jwks.keys = {"key1": {"kid": "key1"}}

    request = MagicMock()
    request.headers.get.return_value = "Bearer token"

    with pytest.raises(HTTPException) as exc_info:
        await middleware._validate_local(request)
    assert exc_info.value.status_code == HTTP_401_UNAUTHORIZED
    assert "JWT expired" in str(exc_info.value.detail)


@pytest.mark.asyncio
@patch("mcp_app.middlewares.jwt_validation.jwt.get_unverified_header")
@patch("mcp_app.middlewares.jwt_validation.jwt.PyJWK")
@patch("mcp_app.middlewares.jwt_validation.jwt.decode")
async def test_validate_local_invalid_token(
    mock_decode: MagicMock, mock_pyjwk: MagicMock, mock_get_header: MagicMock
) -> None:
    """Test _validate_local with invalid token."""
    mock_get_header.return_value = {"kid": "key1"}
    mock_key = MagicMock()
    mock_pyjwk.return_value.key = mock_key
    mock_decode.side_effect = jwt.InvalidTokenError("Invalid token")

    middleware = JWTValidationMiddleware(
        MagicMock(), strategy="local", jwks_uri="https://example.com/jwks"
    )
    assert middleware.jwks is not None
    middleware.jwks.keys = {"key1": {"kid": "key1"}}

    request = MagicMock()
    request.headers.get.return_value = "Bearer token"

    with pytest.raises(HTTPException) as exc_info:
        await middleware._validate_local(request)
    assert exc_info.value.status_code == HTTP_401_UNAUTHORIZED
    assert "Invalid JWT" in str(exc_info.value.detail)


@pytest.mark.asyncio
@patch("mcp_app.middlewares.jwt_validation.jwt.get_unverified_header")
@patch("mcp_app.middlewares.jwt_validation.jwt.PyJWK")
@patch("mcp_app.middlewares.jwt_validation.jwt.decode")
async def test_validate_local_condition_fail(
    mock_decode: MagicMock, mock_pyjwk: MagicMock, mock_get_header: MagicMock
) -> None:
    """Test _validate_local with condition fail."""
    mock_get_header.return_value = {"kid": "key1"}
    mock_key = MagicMock()
    mock_pyjwk.return_value.key = mock_key
    mock_decode.return_value = {"user": "test"}

    middleware = JWTValidationMiddleware(
        MagicMock(),
        strategy="local",
        jwks_uri="https://example.com/jwks",
        allow_conditions=["payload_['user'] == 'admin'"],
    )
    assert middleware.jwks is not None
    middleware.jwks.keys = {"key1": {"kid": "key1"}}

    request = MagicMock()
    request.headers.get.return_value = "Bearer token"

    with pytest.raises(HTTPException) as exc_info:
        await middleware._validate_local(request)
    assert exc_info.value.status_code == HTTP_401_UNAUTHORIZED
    assert "does not meet conditions" in str(exc_info.value.detail)


@pytest.mark.asyncio
@patch("mcp_app.middlewares.jwt_validation.jwt.get_unverified_header")
async def test_validate_local_missing_auth_header(mock_get_header: MagicMock) -> None:  # noqa: ARG001
    """Test _validate_local with missing auth header."""
    middleware = JWTValidationMiddleware(
        MagicMock(), strategy="local", jwks_uri="https://example.com/jwks"
    )
    request = MagicMock()
    request.headers.get.return_value = None

    with pytest.raises(HTTPException) as exc_info:
        await middleware._validate_local(request)
    assert exc_info.value.status_code == HTTP_401_UNAUTHORIZED
    assert "Invalid Authorization header" in str(exc_info.value.detail)


@pytest.mark.asyncio
@patch("mcp_app.middlewares.jwt_validation.jwt.get_unverified_header")
async def test_validate_local_invalid_auth_header(mock_get_header: MagicMock) -> None:  # noqa: ARG001
    """Test _validate_local with invalid auth header."""
    middleware = JWTValidationMiddleware(
        MagicMock(), strategy="local", jwks_uri="https://example.com/jwks"
    )
    request = MagicMock()
    request.headers.get.return_value = "Invalid"

    with pytest.raises(HTTPException) as exc_info:
        await middleware._validate_local(request)
    assert exc_info.value.status_code == HTTP_401_UNAUTHORIZED
    assert "Invalid Authorization header" in str(exc_info.value.detail)


@pytest.mark.asyncio
@patch("mcp_app.middlewares.jwt_validation.jwt.get_unverified_header")
async def test_validate_local_missing_kid(mock_get_header: MagicMock) -> None:
    """Test _validate_local with missing kid."""
    mock_get_header.return_value = {}

    middleware = JWTValidationMiddleware(
        MagicMock(), strategy="local", jwks_uri="https://example.com/jwks"
    )
    request = MagicMock()
    request.headers.get.return_value = "Bearer token"

    with pytest.raises(HTTPException) as exc_info:
        await middleware._validate_local(request)
    assert exc_info.value.status_code == HTTP_401_UNAUTHORIZED
    assert "JWT missing kid" in str(exc_info.value.detail)


@pytest.mark.asyncio
@patch("mcp_app.middlewares.jwt_validation.jwt.get_unverified_header")
@patch("mcp_app.middlewares.jwt_validation.jwt.PyJWK")
@patch("mcp_app.middlewares.jwt_validation.jwt.decode")
async def test_validate_local_success(
    mock_decode: MagicMock, mock_pyjwk: MagicMock, mock_get_header: MagicMock
) -> None:
    """Test _validate_local success."""
    mock_get_header.return_value = {"kid": "key1"}
    mock_key = MagicMock()
    mock_pyjwk.return_value.key = mock_key
    mock_decode.return_value = {"user": "test"}

    middleware = JWTValidationMiddleware(
        MagicMock(), strategy="local", jwks_uri="https://example.com/jwks"
    )
    assert middleware.jwks is not None
    middleware.jwks.keys = {"key1": {"kid": "key1"}}

    request = MagicMock()
    request.headers.get.return_value = "Bearer token"
    request.headers.__dict__["_list"] = []

    await middleware._validate_local(request)

    # jwt.decode is called once in _validate_local
    assert mock_decode.call_count == 1
    assert len(request.headers.__dict__["_list"]) == 1


def test_check_condition_simple() -> None:
    """Test _check_condition with simple condition."""
    middleware = JWTValidationMiddleware(MagicMock())
    payload = {"user": "test"}
    result = middleware._check_condition("payload_['user'] == 'test'", payload)
    assert result is True


def test_check_condition_false() -> None:
    """Test _check_condition with false condition."""
    middleware = JWTValidationMiddleware(MagicMock())
    payload = {"user": "test"}
    result = middleware._check_condition("payload_['user'] == 'other'", payload)
    assert result is False


def test_check_condition_error() -> None:
    """Test _check_condition with error."""
    middleware = JWTValidationMiddleware(MagicMock())
    payload = {"user": "test"}
    result = middleware._check_condition("invalid syntax", payload)
    assert result is False
