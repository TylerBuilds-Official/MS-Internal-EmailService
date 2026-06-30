from utils.auth import Auth


class Validator:
    """Validates that an outbound message targets only allowed internal recipients."""

    def __init__(self, auth: Auth):
        self.auth = auth


    def validate(self, payload: dict) -> dict:
        """Check every to/cc/bcc recipient against the directory of internal users."""

        token            = self.auth.get_token()
        valid_recipients = self.auth.get_valid_recipients()
        recipients       = [address.lower() for address in self._recipient_addresses(payload)]
        invalid          = [address for address in recipients if address not in valid_recipients]

        return {
            'token_acquirable':   bool(token),
            'invalid_recipients': invalid,
            'recipient_ok':       not invalid,
        }


    @staticmethod
    def _recipient_addresses(payload: dict) -> list:
        """Collect the to, cc, and bcc addresses from a composed sendMail payload."""

        message = payload['message']
        fields  = ('toRecipients', 'ccRecipients', 'bccRecipients')

        return [
            entry['emailAddress']['address']
            for field in fields
            for entry in message.get(field, [])
        ]
