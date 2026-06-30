from _errors.email_service_error import EmailServiceError


class AuthenticationError(EmailServiceError):
    """Raised when an access token cannot be acquired from Microsoft Entra ID."""
