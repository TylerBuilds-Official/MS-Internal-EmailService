"""Dependency factories for shared services held on app.state."""

from fastapi import Request

from email_service.email_service import EmailService


def get_email_service(request: Request) -> EmailService:
    """Hand routers the EmailService instance built once in lifespan."""

    return request.app.state.email_service
