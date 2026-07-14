"""Pydantic response models for the email API."""

from pydantic import BaseModel


class SendEmailResponse(BaseModel):
    """Confirmation returned after a message is accepted by Microsoft Graph."""

    status:     str
    recipients: list[str]


class CreateEventRequest(BaseModel):
    """JSON body for POST /create-event (Teams meeting when online_meeting)."""

    subject:          str
    start:            str              # ISO local, e.g. 2026-07-15T09:00
    attendees:        list[str]
    body:             str = ""
    duration_minutes: int = 30
    online_meeting:   bool = True


class CreateEventResponse(BaseModel):
    """Confirmation returned after the event is accepted by Microsoft Graph."""

    status:    str
    attendees: list[str]
