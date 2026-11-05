"""FastAPI application entry point."""


def health() -> dict[str, str]:
    """Return service liveness for GET /health."""
    raise NotImplementedError
