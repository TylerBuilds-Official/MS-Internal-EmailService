"""CORS middleware setup."""

import os

from fastapi                 import FastAPI
from fastapi.middleware.cors import CORSMiddleware


def add_cors(app: FastAPI) -> None:
    """Attach CORSMiddleware. Auth is the X-API-Key header (not cookies), so
    credentials stay off — which also keeps the `*` origin default spec-valid."""

    raw     = os.getenv("CORS_ORIGINS", "*")
    origins = [origin.strip() for origin in raw.split(",") if origin.strip()]

    app.add_middleware(
        CORSMiddleware,
        allow_origins     = origins,
        allow_credentials = False,
        allow_methods     = ["*"],
        allow_headers     = ["*"],
    )
