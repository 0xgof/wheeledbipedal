"""Replay helpers for recorded visualization trajectories."""

from __future__ import annotations

from pathlib import Path
import json

from wheeled_biped_rl.visualization.frame import VisualizationFrame


def load_visualization_frames(trajectory_path: str | Path) -> list[VisualizationFrame]:
    """Load visualization frames from a JSONL trajectory file."""

    loaded_frames = []
    trajectory_text = Path(trajectory_path).read_text(encoding="utf-8")
    for trajectory_line in trajectory_text.splitlines():
        trajectory_record = json.loads(trajectory_line)
        if trajectory_record.get("record_type") != "frame":
            continue
        frame = VisualizationFrame.from_dict(trajectory_record["frame"])
        loaded_frames.append(frame)
    return loaded_frames
