"""FastAPI dependencies — auth and shared-service access."""

from api._dependencies.api_key import require_api_key
from api._dependencies.services import get_email_service


__all__ = [
    "require_api_key",
    "get_email_service",
]
