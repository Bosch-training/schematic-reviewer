"""Confidentiality-safe logging: only allow-listed fields may be logged."""

ALLOWED_FIELDS: frozenset[str] = frozenset(
    {"review_id", "finding_id", "status", "error_type"}
)
LOGGER_NAME: str = "schematic_review"


def configure_logging() -> None:
    """Attach one stream handler to the project logger; idempotent."""
    raise NotImplementedError


def log_event(event: str, /, **fields: object) -> None:
    """Log an event with allow-listed fields; raise ValueError on any other key."""
    raise NotImplementedError
