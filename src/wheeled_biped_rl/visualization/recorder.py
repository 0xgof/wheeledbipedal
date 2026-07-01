"""JSONL trajectory recorder for visualization frames."""

from __future__ import annotations

from pathlib import Path
from typing import Any
import json

from wheeled_biped_rl.observability.logger import JsonlExperimentLogger
from wheeled_biped_rl.visualization.frame import VisualizationFrame


class JsonlTrajectorySink:
    """Append-only JSONL sink for renderable rollout trajectories."""

    def __init__(self,
                 trajectory_path: str | Path,
                 observability_logger: JsonlExperimentLogger | None = None) -> None:
        """Create a sink writing frames to a JSONL path."""

        self.trajectory_path = Path(trajectory_path)
        self.observability_logger = observability_logger
        self._started = False
        self._frame_count = 0

    def start(self, metadata: dict[str, Any]) -> None:
        """Create the trajectory file and write a metadata header row."""

        self.trajectory_path.parent.mkdir(parents=True, exist_ok=True)
        header_record = {
            "record_type": "metadata",
            "metadata": dict(metadata),
        }
        header_line = json.dumps(header_record, sort_keys=True)
        self.trajectory_path.write_text(header_line + "\n", encoding="utf-8")
        self._started = True
        self._frame_count = 0
        if self.observability_logger is not None:
            self.observability_logger.info(
                event_type="trajectory_recording_started",
                message="trajectory recording started",
                payload={
                    "trajectory_path": str(self.trajectory_path),
                    "metadata": dict(metadata),
                })

    def consume(self, frame: VisualizationFrame) -> None:
        """Append one visualization frame row to the trajectory file."""

        if not self._started:
            self.start({})
        frame_record = {
            "record_type": "frame",
            "frame": frame.to_dict(),
        }
        frame_line = json.dumps(frame_record, sort_keys=True)
        with self.trajectory_path.open("a", encoding="utf-8") as trajectory_file:
            trajectory_file.write(frame_line + "\n")
        self._frame_count += 1

    def close(self) -> None:
        """Close the sink.

        The JSONL sink opens files per write, so there is no persistent handle to close.
        """

        if self.observability_logger is not None and self._started:
            self.observability_logger.info(
                event_type="trajectory_recording_closed",
                message="trajectory recording closed",
                payload={
                    "trajectory_path": str(self.trajectory_path),
                    "frame_count": self._frame_count,
                })
        self._started = False
