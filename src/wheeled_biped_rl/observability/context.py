"""Correlation and trace context for experiment observability."""

from __future__ import annotations

from dataclasses import dataclass, replace

from wheeled_biped_rl.observability.ids import (
    make_correlation_id,
    make_span_id,
    make_trace_id,
)


@dataclass(frozen=True)
class TraceContext:
    """Trace identifiers for one operation and its parent relationship."""

    trace_id: str
    span_id: str
    parent_span_id: str | None = None

    def __post_init__(self) -> None:
        """Validate trace identifiers after construction."""

        _require_text("trace_id", self.trace_id)
        _require_text("span_id", self.span_id)

    def child(self) -> "TraceContext":
        """Create a child span that keeps the same trace id."""

        child_trace = TraceContext(trace_id=self.trace_id,
                                   span_id=make_span_id(),
                                   parent_span_id=self.span_id)
        return child_trace


@dataclass(frozen=True)
class ExperimentContext:
    """Correlation fields attached to every experiment log event."""

    run_id: str
    candidate_id: str
    checkpoint_id: str
    phase: str
    correlation_id: str
    trace: TraceContext

    def __post_init__(self) -> None:
        """Validate required experiment correlation fields."""

        _require_text("run_id", self.run_id)
        _require_text("candidate_id", self.candidate_id)
        _require_text("checkpoint_id", self.checkpoint_id)
        _require_text("phase", self.phase)
        _require_text("correlation_id", self.correlation_id)

    def child_span(self, phase: str) -> "ExperimentContext":
        """Create a context for a nested operation under the same correlation id."""

        child_context = replace(self, phase=phase, trace=self.trace.child())
        return child_context


def make_experiment_context(run_id: str,
                            candidate_id: str,
                            checkpoint_id: str,
                            phase: str) -> ExperimentContext:
    """Create a new root experiment context with generated correlation and trace ids."""

    trace = TraceContext(trace_id=make_trace_id(), span_id=make_span_id())
    context = ExperimentContext(run_id=run_id,
                                candidate_id=candidate_id,
                                checkpoint_id=checkpoint_id,
                                phase=phase,
                                correlation_id=make_correlation_id(),
                                trace=trace)
    return context


def _require_text(field_name: str,
                  field_value: str) -> None:
    """Require a non-empty string field."""

    if not isinstance(field_value, str) or not field_value:
        raise ValueError(f"{field_name} is required")
