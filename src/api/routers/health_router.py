"""Health endpoint — liveness probe (public, no auth, dependency-free)."""

from fastapi import APIRouter


router = APIRouter(tags=["Health"])


@router.get("/health")
def health() -> dict:
    """Return a static OK payload."""

    return {"status": "ok"}
