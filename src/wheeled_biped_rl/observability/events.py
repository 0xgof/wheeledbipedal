"""Structured observability events for experiment debugging."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from wheeled_biped_rl.observability.context import ExperimentContext
from wheeled_biped_rl.observability.time import utc_timestamp

_ALLOWED_LEVELS = {"debug", "info", "warning", "error", "critical"}


@dataclass(frozen=True)
class ObservabilityEvent:
    """One structured event in an experiment observability stream."""

    timestamp: str
    level: str
    event_type: str
    message: str
    run_id: str
    candidate_id: str
    checkpoint_id: str
    phase: str
    correlation_id: str
    trace_id: str
    span_id: str
    parent_span_id: str | None = None
    step: int | None = None
    episode: int | None = None
    metrics: dict[str, float] = field(default_factory=dict)
    payload: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Validate required event fields and severity level."""

        _require_text("timestamp", self.timestamp)
        if self.level not in _ALLOWED_LEVELS:
            raise ValueError(f"level must be one of {sorted(_ALLOWED_LEVELS)}")
        _require_text("event_type", self.event_type)
        _require_text("message", self.message)
        _require_text("run_id", self.run_id)
        _require_text("candidate_id", self.candidate_id)
        _require_text("checkpoint_id", self.checkpoint_id)
        _require_text("phase", self.phase)
        _require_text("correlation_id", self.correlation_id)
        _require_text("trace_id", self.trace_id)
        _require_text("span_id", self.span_id)
        if self.step is not None and self.step < 0:
            raise ValueError("step must be non-negative")
        if self.episode is not None and self.episode < 0:
            raise ValueError("episode must be non-negative")

    @classmethod
    def from_context(cls,
                     context: ExperimentContext,
                     event_type: str,
                     message: str,
                     level: str = "info",
                     step: int | None = None,
                     episode: int | None = None,
                     metrics: dict[str, float] | None = None,
                     payload: dict[str, Any] | None = None) -> "ObservabilityEvent":
        """Create an event using an experiment context."""

        event = cls(timestamp=utc_timestamp(),
                    level=level,
                    event_type=event_type,
                    message=message,
                    run_id=context.run_id,
                    candidate_id=context.candidate_id,
                    checkpoint_id=context.checkpoint_id,
                    phase=context.phase,
                    correlation_id=context.correlation_id,
                    trace_id=context.trace.trace_id,
                    span_id=context.trace.span_id,
                    parent_span_id=context.trace.parent_span_id,
                    step=step,
                    episode=episode,
                    metrics={} if metrics is None else dict(metrics),
                    payload={} if payload is None else dict(payload))
        return event

    def to_dict(self) -> dict[str, Any]:
        """Serialize the event to a stable JSON-compatible dictionary."""

        event_dict = {
            "timestamp": self.timestamp,
            "level": self.level,
            "event_type": self.event_type,
            "message": self.message,
            "run_id": self.run_id,
            "candidate_id": self.candidate_id,
            "checkpoint_id": self.checkpoint_id,
            "phase": self.phase,
            "correlation_id": self.correlation_id,
            "trace_id": self.trace_id,
            "span_id": self.span_id,
            "parent_span_id": self.parent_span_id,
            "step": self.step,
            "episode": self.episode,
            "metrics": dict(self.metrics),
            "payload": dict(self.payload),
        }
        return event_dict

    @classmethod
    def from_dict(cls, event_dict: dict[str, Any]) -> "ObservabilityEvent":
        """Reconstruct and validate an event from serialized fields."""

        event = cls(timestamp=event_dict["timestamp"],
                    level=event_dict["level"],
                    event_type=event_dict["event_type"],
                    message=event_dict["message"],
                    run_id=event_dict["run_id"],
                    candidate_id=event_dict["candidate_id"],
                    checkpoint_id=event_dict["checkpoint_id"],
                    phase=event_dict["phase"],
                    correlation_id=event_dict["correlation_id"],
                    trace_id=event_dict["trace_id"],
                    span_id=event_dict["span_id"],
                    parent_span_id=event_dict.get("parent_span_id"),
                    step=event_dict.get("step"),
                    episode=event_dict.get("episode"),
                    metrics=dict(event_dict.get("metrics", {})),
                    payload=dict(event_dict.get("payload", {})))
        return event


def _require_text(field_name: str,
                  field_value: str) -> None:
    """Require a non-empty string field."""

    if not isinstance(field_value, str) or not field_value:
        raise ValueError(f"{field_name} is required")
