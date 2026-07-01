"""Time helpers for structured observability events."""

from __future__ import annotations

from datetime import datetime, timezone


def utc_timestamp() -> str:
    """Return an ISO-8601 UTC timestamp with a ``Z`` suffix."""

    timestamp = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    return timestamp
