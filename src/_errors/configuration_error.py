from src._errors.email_service_error import EmailServiceError


class ConfigurationError(EmailServiceError):
    """Raised when required environment configuration is missing or blank."""
