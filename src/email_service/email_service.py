import os

from utils.auth import Auth
from utils.compose import compose
from utils.send import send_email
from utils.validate import Validator
from _errors.invalid_recipient_error import InvalidRecipientError


class EmailService:
    """Sends internal email via Microsoft Graph, restricting recipients to directory users."""

    def __init__(self):
        self.auth      = Auth()
        self.validator = Validator(self.auth)


    def send_email(self, to: str | list[str], subject: str, body: str, **kwargs) -> None:
        """Validate all recipients, then send the message; raises on validation or send failure."""

        recipients = [to] if isinstance(to, str) else list(to)
        recipients = [address.lower() for address in recipients]
        payload    = compose(recipients, subject, body, **kwargs)
        result     = self.validator.validate(payload)

        if not result['recipient_ok']:
            company = os.getenv('COMPANY_NAME', 'the organization')
            invalid = ', '.join(result['invalid_recipients'])
            raise InvalidRecipientError(f"Recipient(s) not internal to {company}: {invalid}")

        send_email(payload=payload, auth=self.auth)
