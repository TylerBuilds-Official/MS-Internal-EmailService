"""Construct the FastAPI app with CORS, lifespan, and routers wired in."""
import os

from fastapi import FastAPI

from api.build.cors            import add_cors
from api.build.lifespan        import lifespan
from api.routers.route_manager import RouteManager


def build_api() -> FastAPI:
    """Build and return the FastAPI app instance."""

    app = FastAPI(
        title       = f"{os.getenv('COMPANY_NAME')}: Internal Email API",
        description = "Internal email relay over Microsoft Graph. Recipients are restricted to tenant directory users.",
        version     = "0.1.0",
        lifespan    = lifespan,
    )

    add_cors(app)
    RouteManager(app).register_routes()

    return app
