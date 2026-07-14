"""Pydantic API models — request/response shapes."""

from api._models.email_models import (
    CreateEventRequest,
    CreateEventResponse,
    SendEmailResponse,
)


__all__ = ["CreateEventRequest", "CreateEventResponse", "SendEmailResponse"]
