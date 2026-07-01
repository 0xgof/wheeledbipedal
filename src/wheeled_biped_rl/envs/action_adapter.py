"""Action adaptation for the foundational Gymnasium environment.

This module is the boundary between normalized policy output and robot-domain
actuator commands. The environment should pass actions through this adapter
before any backend sees them.
"""

from __future__ import annotations

import numpy as np
from gymnasium import spaces

from wheeled_biped_rl.simulation.mechanism_config import RobotMechanismConfig
from wheeled_biped_rl.simulation.robot_state import RobotAction


class ActionAdapter:
    """Convert normalized policy actions into actuator-domain commands.

    The public action space is a four-channel ``Box(-1, 1)`` in the configured
    action order. Hip channels become position targets; wheel channels become
    torque-like commands scaled by the mechanism actuator limits.
    """

    def __init__(self, mechanism_config: RobotMechanismConfig) -> None:
        """Create an adapter using configured joint and actuator limits."""

        self.mechanism_config = mechanism_config
        self.space = spaces.Box(low=-1.0,
                                high=1.0,
                                shape=(len(mechanism_config.action_order),),
                                dtype=np.float32)

    def adapt(self, action: np.ndarray) -> RobotAction:
        """Clip and scale one normalized action vector.

        Args:
            action: Policy output with shape matching ``self.space.shape``.

        Returns:
            ``RobotAction`` in actuator units for the current reduced model.

        Raises:
            ValueError: If the provided action does not match the expected shape.
        """

        action_array = np.asarray(action, dtype=np.float32)
        if action_array.shape != self.space.shape:
            raise ValueError(f"action shape must be {self.space.shape}")

        clipped_action = np.clip(action_array, self.space.low, self.space.high)
        hip_scale_rad = self._hip_scale_rad()
        wheel_scale_nm = self.mechanism_config.actuators.wheel_max_torque_nm
        robot_action = RobotAction(
            left_hip=float(clipped_action[0] * hip_scale_rad),
            right_hip=float(clipped_action[1] * hip_scale_rad),
            left_wheel=float(clipped_action[2] * wheel_scale_nm),
            right_wheel=float(clipped_action[3] * wheel_scale_nm))
        return robot_action

    def _hip_scale_rad(self) -> float:
        """Return the symmetric hip target scale allowed by both hip limits."""

        lower_limit_abs = abs(self.mechanism_config.hip_limit_lower_rad)
        upper_limit_abs = abs(self.mechanism_config.hip_limit_upper_rad)
        hip_scale_rad = min(lower_limit_abs, upper_limit_abs)
        return hip_scale_rad
