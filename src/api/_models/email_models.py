"""Pydantic response models for the email API."""

from pydantic import BaseModel


class SendEmailResponse(BaseModel):
    """Confirmation returned after a message is accepted by Microsoft Graph."""

    status:     str
    recipients: list[str]
