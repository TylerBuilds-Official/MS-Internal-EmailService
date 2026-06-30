from _errors.graph_api_error import GraphApiError


class EmailSendError(GraphApiError):
    """Raised when Microsoft Graph rejects a sendMail request."""
