"""RouteManager — central registry for every APIRouter mounted on the app.

Adding a new router is two lines: import it at the top of this file and
append it to `self.routes` in __init__.
"""
import logging

from fastapi import FastAPI

from api.routers.health_router import router as health_router
from api.routers.email_router  import router as email_router


logger = logging.getLogger(__name__)


class RouteManager:
    """Central registry for every APIRouter mounted on the FastAPI app."""

    def __init__(self, app: FastAPI) -> None:
        self.app    = app
        self.routes = [
            health_router,
            email_router,
        ]


    def register_routes(self) -> None:
        """Mount every router in self.routes onto the FastAPI app."""

        if not self.routes:
            logger.warning("No routers to register")

            return

        for router in self.routes:
            self.app.include_router(router)
            logger.info(f"Registered router tags={router.tags}")

        logger.info(f"Registered {len(self.routes)} routers")
