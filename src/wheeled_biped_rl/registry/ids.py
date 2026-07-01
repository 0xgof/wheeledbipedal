"""Identifier helpers for controller-candidate registry records."""

from __future__ import annotations

from datetime import datetime, timezone
import re
from uuid import uuid4

_SLUG_PATTERN = re.compile(r"[^a-z0-9]+")


def _slugify(label: str) -> str:
    """Convert a free-form label into a lowercase identifier fragment."""

    lowered_label = label.lower().strip()
    normalized_label = _SLUG_PATTERN.sub("_", lowered_label).strip("_")
    if not normalized_label:
        normalized_label = "candidate"
    return normalized_label


def _timestamp() -> str:
    """Return the UTC timestamp component used in generated registry ids."""

    created_at = datetime.now(timezone.utc)
    timestamp = created_at.strftime("%Y%m%d_%H%M%S")
    return timestamp


def _short_token() -> str:
    """Return a short random suffix to avoid local id collisions."""

    token = uuid4().hex[:6]
    return token


def make_candidate_id(label: str) -> str:
    """Create a controller-candidate id from a human-readable label."""

    candidate_id = f"cand_{_timestamp()}_{_slugify(label)}_{_short_token()}"
    return candidate_id


def make_run_id(label: str) -> str:
    """Create a training/evaluation run id from a human-readable label."""

    run_id = f"run_{_timestamp()}_{_slugify(label)}_{_short_token()}"
    return run_id
