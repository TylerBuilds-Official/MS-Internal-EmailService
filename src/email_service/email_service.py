import os

from src.utils.auth import Auth
from src.utils.compose import compose
from src.utils.send import send_email
from src.utils.validate import Validator
from src._errors.invalid_recipient_error import InvalidRecipientError


class EmailService:
    """Sends internal email via Microsoft Graph, restricting recipients to directory users."""

    def __init__(self):
        self.auth      = Auth()
        self.validator = Validator(self.auth)


    def send_email(self, to: str, subject: str, body: str, **kwargs) -> None:
        """Validate all recipients, then send the message; raises on validation or send failure."""

        to      = to.lower()
        payload = compose(to, subject, body, **kwargs)
        result  = self.validator.validate(payload)

        if not result['recipient_ok']:
            company = os.getenv('COMPANY_NAME', 'the organization')
            invalid = ', '.join(result['invalid_recipients'])
            raise InvalidRecipientError(f"Recipient(s) not internal to {company}: {invalid}")

        send_email(payload=payload, auth=self.auth)
