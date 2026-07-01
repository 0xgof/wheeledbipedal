"""JSONL experiment logger for structured observability events."""

from __future__ import annotations

from pathlib import Path
from typing import Any
import json

from wheeled_biped_rl.observability.context import ExperimentContext
from wheeled_biped_rl.observability.events import ObservabilityEvent


class JsonlExperimentLogger:
    """Append-only JSONL writer for experiment observability."""

    def __init__(self, log_path: str | Path) -> None:
        """Create a logger that writes one JSON record per line."""

        self.log_path = Path(log_path)
        self.context: ExperimentContext | None = None
        self.started = False

    def start(self,
              context: ExperimentContext,
              metadata: dict[str, Any]) -> None:
        """Start a log stream with metadata and a root experiment context."""

        self.log_path.parent.mkdir(parents=True, exist_ok=True)
        self.context = context
        metadata_record = {
            "record_type": "metadata",
            "context": _context_to_dict(context),
            "metadata": dict(metadata),
        }
        metadata_line = json.dumps(metadata_record, sort_keys=True)
        self.log_path.write_text(metadata_line + "\n", encoding="utf-8")
        self.started = True

    def debug(self,
              event_type: str,
              message: str,
              step: int | None = None,
              episode: int | None = None,
              metrics: dict[str, float] | None = None,
              payload: dict[str, Any] | None = None) -> ObservabilityEvent:
        """Write a debug-level event."""

        event = self._write_event(event_type=event_type,
                                  message=message,
                                  level="debug",
                                  step=step,
                                  episode=episode,
                                  metrics=metrics,
                                  payload=payload)
        return event

    def info(self,
             event_type: str,
             message: str,
             step: int | None = None,
             episode: int | None = None,
             metrics: dict[str, float] | None = None,
             payload: dict[str, Any] | None = None) -> ObservabilityEvent:
        """Write an info-level event."""

        event = self._write_event(event_type=event_type,
                                  message=message,
                                  level="info",
                                  step=step,
                                  episode=episode,
                                  metrics=metrics,
                                  payload=payload)
        return event

    def exception(self,
                  event_type: str,
                  message: str,
                  exc: BaseException,
                  step: int | None = None,
                  episode: int | None = None,
                  payload: dict[str, Any] | None = None) -> ObservabilityEvent:
        """Write an error event with exception metadata."""

        exception_payload = {} if payload is None else dict(payload)
        exception_payload["exception_type"] = type(exc).__name__
        exception_payload["exception_message"] = str(exc)
        event = self._write_event(event_type=event_type,
                                  message=message,
                                  level="error",
                                  step=step,
                                  episode=episode,
                                  metrics=None,
                                  payload=exception_payload)
        return event

    def close(self) -> None:
        """Close the logger.

        The logger opens the file per write, so closing marks the stream inactive.
        """

        self.started = False

    def _write_event(self,
                     event_type: str,
                     message: str,
                     level: str,
                     step: int | None,
                     episode: int | None,
                     metrics: dict[str, float] | None,
                     payload: dict[str, Any] | None) -> ObservabilityEvent:
        """Create and append one event to the JSONL stream."""

        context = self._require_context()
        event = ObservabilityEvent.from_context(context=context,
                                                event_type=event_type,
                                                message=message,
                                                level=level,
                                                step=step,
                                                episode=episode,
                                                metrics=metrics,
                                                payload=payload)
        event_record = {
            "record_type": "event",
            "event": event.to_dict(),
        }
        event_line = json.dumps(event_record, sort_keys=True)
        with self.log_path.open("a", encoding="utf-8") as log_file:
            log_file.write(event_line + "\n")
        return event

    def _require_context(self) -> ExperimentContext:
        """Return the active context or fail if the stream has not started."""

        if self.context is None:
            raise RuntimeError("logger.start must be called before logging events")
        return self.context


def _context_to_dict(context: ExperimentContext) -> dict[str, Any]:
    """Serialize an experiment context for metadata records."""

    context_dict = {
        "run_id": context.run_id,
        "candidate_id": context.candidate_id,
        "checkpoint_id": context.checkpoint_id,
        "phase": context.phase,
        "correlation_id": context.correlation_id,
        "trace_id": context.trace.trace_id,
        "span_id": context.trace.span_id,
        "parent_span_id": context.trace.parent_span_id,
    }
    return context_dict
