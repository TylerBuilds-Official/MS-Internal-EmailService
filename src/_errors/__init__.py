"""Custom exceptions raised by the email service."""

from _errors.email_service_error import EmailServiceError
from _errors.configuration_error import ConfigurationError
from _errors.authentication_error import AuthenticationError
from _errors.graph_api_error import GraphApiError
from _errors.email_send_error import EmailSendError
from _errors.invalid_recipient_error import InvalidRecipientError


__all__ = [
    "EmailServiceError",
    "ConfigurationError",
    "AuthenticationError",
    "GraphApiError",
    "EmailSendError",
    "InvalidRecipientError",
]
