"""API-key auth — validates the X-API-Key header against the API_KEY env var."""

import os
import secrets

from fastapi          import Security, HTTPException, status
from fastapi.security import APIKeyHeader


api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


def require_api_key(provided: str | None = Security(api_key_header)) -> None:
    """Reject the request unless the X-API-Key header matches the configured API_KEY."""

    expected = os.getenv("API_KEY")

    if not expected:
        raise HTTPException(
            status_code = status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail      = "Server API key is not configured.",
        )

    if not provided or not secrets.compare_digest(provided, expected):
        raise HTTPException(
            status_code = status.HTTP_401_UNAUTHORIZED,
            detail      = "Invalid or missing API key.",
        )
