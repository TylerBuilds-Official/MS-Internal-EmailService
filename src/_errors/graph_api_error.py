from src._errors.email_service_error import EmailServiceError


class GraphApiError(EmailServiceError):
    """Raised when a Microsoft Graph request returns an unsuccessful response."""

    def __init__(self, message: str, status_code: int | None = None, response_text: str | None = None):
        self.status_code   = status_code
        self.response_text = response_text
        super().__init__(message)
