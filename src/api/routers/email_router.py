"""
Email send endpoint for the internal email API.

  POST /send  — send an internal email via Microsoft Graph (API-key protected).

multipart/form-data so attachments can ride along as real file parts. Repeat
the `to` / `cc` / `bcc` form fields to add multiple recipients. Every recipient
is validated against the tenant directory in the service layer; a non-internal
address rejects the whole send with 400.

The handler is sync `def` on purpose: EmailService does blocking Graph I/O, so
FastAPI runs it in its threadpool and the event loop stays responsive.
"""
import base64
import logging
from pathlib import Path
from typing import Literal

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status

from api._dependencies import get_email_service, require_api_key
from api._models       import CreateEventRequest, CreateEventResponse, SendEmailResponse
from email_service.email_service import EmailService
from _errors import (
    AuthenticationError,
    ConfigurationError,
    GraphApiError,
    InvalidRecipientError,
)


logger = logging.getLogger(__name__)


router = APIRouter(tags=["email"], dependencies=[Depends(require_api_key)])


@router.post("/send", response_model=SendEmailResponse)
def send(
        to:        list[str]               = Form(..., description="Recipient address; repeat to add more"),
        subject:   str                     = Form(...),
        body:      str                     = Form(...),
        cc:        list[str] | None        = Form(default=None, description="CC address; repeat to add more"),
        bcc:       list[str] | None        = Form(default=None, description="BCC address; repeat to add more"),
        body_type: Literal["Text", "HTML"] = Form(default="Text", description="Message body content type"),
        files:     list[UploadFile]        = File(default=[], description="Optional file attachments"),
        inline:    list[str] | None        = Form(default=None, description=(
            "Filename(s) among `files` to embed inline instead of attaching; reference "
            "them in an HTML body as cid:<filename stem> (logo.png -> cid:logo)")),
        service:   EmailService            = Depends(get_email_service) ) -> SendEmailResponse:
    """Send an internal email. All recipients must be tenant directory users."""

    inline_names = set(inline or [])
    attachments  = [_to_graph_attachment(upload, inline_names) for upload in files]

    try:
        service.send_email(
            to          = to,
            subject     = subject,
            body        = body,
            cc          = cc,
            bcc         = bcc,
            body_type   = body_type,
            attachments = attachments or None,
        )
    except InvalidRecipientError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e
    except ConfigurationError as e:
        logger.error(f"Email service misconfigured: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)) from e
    except (AuthenticationError, GraphApiError) as e:
        logger.error(f"Upstream Microsoft Graph failure: {e}")
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(e)) from e

    return SendEmailResponse(status="sent", recipients=to + (cc or []) + (bcc or []))


@router.post("/create-event", response_model=CreateEventResponse)
def create_event(
        request: CreateEventRequest,
        service: EmailService = Depends(get_email_service) ) -> CreateEventResponse:
    """Create a calendar event with invites (a Teams meeting when online_meeting).

    Attendees must be tenant directory users — the same internal-only rule as
    /send. Requires APPLICATION Calendars.ReadWrite on the app registration;
    the event lands on the service sender's calendar as organizer.
    """

    try:
        service.create_event(
            subject          = request.subject,
            start_iso        = request.start,
            attendees        = request.attendees,
            body             = request.body,
            duration_minutes = request.duration_minutes,
            online_meeting   = request.online_meeting,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail=f"Invalid start datetime: {e}") from e
    except InvalidRecipientError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e
    except ConfigurationError as e:
        logger.error(f"Email service misconfigured: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)) from e
    except (AuthenticationError, GraphApiError) as e:
        logger.error(f"Upstream Microsoft Graph failure: {e}")
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(e)) from e

    return CreateEventResponse(status="created", attendees=request.attendees)


def _to_graph_attachment(upload: UploadFile, inline_names: set[str]) -> dict:
    """Read an uploaded file into a base64-encoded Graph fileAttachment object.

    Files named in `inline_names` become inline attachments: hidden from the
    attachment list and addressable from the HTML body via cid:<filename stem>.
    """

    content    = upload.file.read()
    attachment = {
        "@odata.type":  "#microsoft.graph.fileAttachment",
        "name":         upload.filename,
        "contentType":  upload.content_type or "application/octet-stream",
        "contentBytes": base64.b64encode(content).decode("utf-8"),
    }

    if upload.filename in inline_names:
        attachment["isInline"]  = True
        attachment["contentId"] = Path(upload.filename).stem

    return attachment
