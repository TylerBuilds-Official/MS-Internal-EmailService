"""Application lifespan hooks — owns shared resources for the process lifetime."""

import logging

from contextlib import asynccontextmanager

from fastapi import FastAPI

from email_service.email_service import EmailService


logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Build the shared EmailService once and expose it on app.state.

    EmailService construction validates configuration and builds the MSAL
    app, so a misconfigured deployment fails fast at startup rather than on
    the first request. No network calls happen here.
    """

    logger.info("[API] (lifespan): startup — building EmailService")
    app.state.email_service = EmailService()

    try:
        yield
    finally:
        logger.info("[API] (lifespan): shutdown")
