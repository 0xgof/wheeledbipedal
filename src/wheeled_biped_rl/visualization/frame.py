"""Serializable visualization frame records."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from wheeled_biped_rl.visualization.render_state import RenderState


@dataclass(frozen=True)
class VisualizationFrame:
    """One renderable rollout frame plus optional training/debug metadata."""

    render_state: RenderState
    action: tuple[float, ...] | None = None
    reward: float | None = None
    terminated: bool = False
    truncated: bool = False
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Serialize a visualization frame to JSON-compatible data."""

        action_values = None
        if self.action is not None:
            action_values = list(self.action)
        frame_dict = {
            "render_state": self.render_state.to_dict(),
            "action": action_values,
            "reward": self.reward,
            "terminated": self.terminated,
            "truncated": self.truncated,
            "metadata": dict(self.metadata),
        }
        return frame_dict

    @classmethod
    def from_dict(cls, frame_dict: dict[str, Any]) -> "VisualizationFrame":
        """Reconstruct a visualization frame from serialized fields."""

        action = frame_dict.get("action")
        action_values = None
        if action is not None:
            action_values = tuple(float(action_value) for action_value in action)
        frame = cls(
            render_state=RenderState.from_dict(frame_dict["render_state"]),
            action=action_values,
            reward=frame_dict.get("reward"),
            terminated=bool(frame_dict.get("terminated", False)),
            truncated=bool(frame_dict.get("truncated", False)),
            metadata=dict(frame_dict.get("metadata", {})))
        return frame
