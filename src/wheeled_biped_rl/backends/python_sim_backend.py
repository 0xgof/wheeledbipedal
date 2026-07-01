"""Deterministic Python backend for the foundational Gymnasium API.

This backend wraps the simple reduced dynamics model while keeping the
Gymnasium environment independent from integration details.
"""

from __future__ import annotations

from wheeled_biped_rl.backends.base_backend import BackendStep
from wheeled_biped_rl.simulation.mechanism_config import RobotMechanismConfig
from wheeled_biped_rl.simulation.simple_dynamics import SimpleDynamics
from wheeled_biped_rl.simulation.robot_state import RobotAction, RobotState


class PythonSimBackend:
    """Deterministic backend using the simple Layer 1 reduced dynamics."""

    def __init__(self, mechanism_config: RobotMechanismConfig) -> None:
        """Create a backend from the resolved mechanism configuration."""

        self.mechanism_config = mechanism_config
        self.dynamics = SimpleDynamics(mechanism_config)
        self.state = self.dynamics.reset(seed=None)

    def reset(self, seed: int | None = None) -> RobotState:
        """Reset to a deterministic near-upright state."""

        self.state = self.dynamics.reset(seed=seed)
        return self.state

    def step(self,
             action: RobotAction,
             dt_s: float) -> BackendStep:
        """Advance the wrapped reduced dynamics model by one step."""

        dynamics_step = self.dynamics.step(robot_state=self.state,
                                           action=action,
                                           dt_s=dt_s)
        self.state = dynamics_step.state
        backend_step = BackendStep(state=dynamics_step.state,
                                   diagnostics=dynamics_step.diagnostics)
        return backend_step

    def close(self) -> None:
        """Release backend resources."""

        return None
