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
from typing import Literal

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status

from api._dependencies import get_email_service, require_api_key
from api._models       import SendEmailResponse
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
        service:   EmailService            = Depends(get_email_service) ) -> SendEmailResponse:
    """Send an internal email. All recipients must be tenant directory users."""

    attachments = [_to_graph_attachment(upload) for upload in files]

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


def _to_graph_attachment(upload: UploadFile) -> dict:
    """Read an uploaded file into a base64-encoded Graph fileAttachment object."""

    content = upload.file.read()

    return {
        "@odata.type":  "#microsoft.graph.fileAttachment",
        "name":         upload.filename,
        "contentType":  upload.content_type or "application/octet-stream",
        "contentBytes": base64.b64encode(content).decode("utf-8"),
    }
