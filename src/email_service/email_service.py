import os

from utils.auth import Auth
from utils.compose import compose
from utils.events import create_event
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


    def create_event(
            self,
            subject: str,
            start_iso: str,
            attendees: str | list[str],
            body: str = '',
            duration_minutes: int = 30,
            online_meeting: bool = True ) -> None:
        """Validate all attendees (directory users only), then create the calendar
        event (Teams meeting when online_meeting); raises on validation or Graph failure."""

        invited = [attendees] if isinstance(attendees, str) else list(attendees)
        invited = [address.lower() for address in invited]

        # Reuse the sendMail validator by shaping the attendees as recipients —
        # the same internal-directory-only guarantee applies to invites.
        result = self.validator.validate(compose(invited, subject, body or subject))
        if not result['recipient_ok']:
            company = os.getenv('COMPANY_NAME', 'the organization')
            invalid = ', '.join(result['invalid_recipients'])
            raise InvalidRecipientError(f"Attendee(s) not internal to {company}: {invalid}")

        create_event(
            subject          = subject,
            start_iso        = start_iso,
            attendees        = invited,
            body             = body,
            duration_minutes = duration_minutes,
            online_meeting   = online_meeting,
            auth             = self.auth,
        )
