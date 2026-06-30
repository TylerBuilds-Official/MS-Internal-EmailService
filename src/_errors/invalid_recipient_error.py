from src._errors.email_service_error import EmailServiceError


class InvalidRecipientError(EmailServiceError):
    """Raised when a recipient is not an allowed internal directory user."""
