"""Identifier helpers for experiment observability."""

from __future__ import annotations

import uuid


def make_correlation_id() -> str:
    """Create an id that correlates all logs for one experiment attempt."""

    correlation_id = f"corr_{uuid.uuid4().hex}"
    return correlation_id


def make_trace_id() -> str:
    """Create an id for a trace spanning related experiment operations."""

    trace_id = f"trace_{uuid.uuid4().hex}"
    return trace_id


def make_span_id() -> str:
    """Create an id for one operation inside a trace."""

    span_id = f"span_{uuid.uuid4().hex}"
    return span_id
