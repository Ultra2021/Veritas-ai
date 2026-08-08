"""API route definitions for Veritas AI Backend."""

from fastapi import APIRouter

router = APIRouter()


@router.get("/")
def read_root() -> dict[str, str]:
    """Root endpoint confirming the service is running."""
    return {"status": "running", "project": "Veritas AI Backend"}


@router.get("/health")
def health_check() -> dict[str, str]:
    """Health check endpoint for uptime and load balancer probes."""
    return {"status": "healthy"}
