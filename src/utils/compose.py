import base64
import mimetypes
from pathlib import Path


def compose(
        to: str | list[str],
        subject: str,
        body: str,
        cc: str | list[str] | None = None,
        bcc: str | list[str] | None = None,
        attachments: list | None = None,
        body_type: str = 'Text' ) -> dict:
    """Build a Microsoft Graph sendMail payload from the given message fields."""

    message = {
        "subject": subject,
        "body": {
            "contentType": body_type,
            "content": body,
        },
        "toRecipients": _recipients(to),
    }

    if cc:
        message["ccRecipients"] = _recipients(cc)
    if bcc:
        message["bccRecipients"] = _recipients(bcc)
    if attachments:
        message["attachments"] = _attachments(attachments)

    return {
        "message": message,
        "saveToSentItems": True,
    }


def _recipients(addresses: str | list[str]) -> list:
    """Normalize a string or list of addresses into Graph recipient objects."""

    if isinstance(addresses, str):
        addresses = [addresses]

    return [{"emailAddress": {"address": address}} for address in addresses]


def _attachments(attachments: list) -> list:
    """Build Graph attachment objects, passing through dicts already in Graph format."""

    return [item if isinstance(item, dict) else _file_attachment(item) for item in attachments]


def _file_attachment(path: str) -> dict:
    """Read a file from disk into a base64-encoded Graph fileAttachment object."""

    file_path    = Path(path)
    content_type = mimetypes.guess_type(file_path.name)[0] or 'application/octet-stream'
    content      = base64.b64encode(file_path.read_bytes()).decode('utf-8')

    return {
        "@odata.type": "#microsoft.graph.fileAttachment",
        "name": file_path.name,
        "contentType": content_type,
        "contentBytes": content,
    }
