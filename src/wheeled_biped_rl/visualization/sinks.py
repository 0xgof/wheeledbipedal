"""Visualization sink protocol for pluggable viewers and recorders."""

from __future__ import annotations

from typing import Any, Protocol

from wheeled_biped_rl.visualization.frame import VisualizationFrame


class VisualizationSink(Protocol):
    """Protocol implemented by recorders, RViz bridges, and local viewers."""

    def start(self, metadata: dict[str, Any]) -> None:
        """Start a visualization stream with run-level metadata."""

    def consume(self, frame: VisualizationFrame) -> None:
        """Consume one renderable visualization frame."""

    def close(self) -> None:
        """Close the visualization stream and release resources."""
