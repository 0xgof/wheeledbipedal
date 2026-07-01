"""Actor observation construction for the foundational environment.

The builder owns the deployable observation contract. It intentionally emits
only actor-safe values and keeps privileged simulator diagnostics out of the
policy input.
"""

from __future__ import annotations

import numpy as np
from gymnasium import spaces

from wheeled_biped_rl.simulation.mechanism_config import RobotMechanismConfig
from wheeled_biped_rl.simulation.robot_state import RobotState


class ObservationBuilder:
    """Build deployable actor observations from reduced robot state.

    The current vector contains motor positions, motor velocities, previous
    action, and IMU-like pitch/rate slots. Roll values are present as zeros until
    a later model exposes lateral dynamics.
    """

    observation_size = 16

    def __init__(self, mechanism_config: RobotMechanismConfig) -> None:
        """Create a builder for the configured actor observation contract."""

        self.mechanism_config = mechanism_config
        self.space = spaces.Box(low=-np.inf,
                                high=np.inf,
                                shape=(self.observation_size,),
                                dtype=np.float32)

    def build(self, robot_state: RobotState) -> np.ndarray:
        """Return the actor observation vector as ``float32``.

        Args:
            robot_state: Reduced state after reset or a backend step.

        Returns:
            Observation matching ``self.space`` and suitable for Gymnasium.
        """

        observation_values = [
            robot_state.left_hip_rad,
            robot_state.right_hip_rad,
            robot_state.left_wheel_rad,
            robot_state.right_wheel_rad,
            robot_state.left_hip_rad_s,
            robot_state.right_hip_rad_s,
            robot_state.left_wheel_rad_s,
            robot_state.right_wheel_rad_s,
            robot_state.previous_action.left_hip,
            robot_state.previous_action.right_hip,
            robot_state.previous_action.left_wheel,
            robot_state.previous_action.right_wheel,
            robot_state.body_pitch_rad,
            0.0,
            robot_state.body_pitch_rad_s,
            0.0,
        ]
        observation = np.asarray(observation_values, dtype=np.float32)
        return observation
