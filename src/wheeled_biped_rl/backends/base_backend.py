"""Backend protocol used by Gymnasium environments.

The environment owns RL-facing orchestration. Backends own state reset and state
advance so the same environment surface can later be connected to richer Layer 1
or Layer 2 simulators without changing the policy-facing API.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from wheeled_biped_rl.simulation.robot_state import RobotAction, RobotState


@dataclass(frozen=True)
class BackendStep:
    """State transition returned by a simulation backend step."""

    state: RobotState
    diagnostics: dict[str, float | bool | str]


class BaseBackend(Protocol):
    """Protocol for deterministic environment backends."""

    def reset(self, seed: int | None = None) -> RobotState:
        """Reset backend state and return the initial robot state."""

    def step(self,
             action: RobotAction,
             dt_s: float) -> BackendStep:
        """Advance backend state by one environment step."""

    def close(self) -> None:
        """Release backend resources."""
