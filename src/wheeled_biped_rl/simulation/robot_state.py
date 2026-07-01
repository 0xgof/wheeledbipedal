"""State and action records for the reduced-order wheeled-biped model."""

from __future__ import annotations

from dataclasses import dataclass

from wheeled_biped_rl.simulation.mechanism_config import RobotMechanismConfig


@dataclass(frozen=True)
class RobotAction:
    """Four-channel actuator command used by the foundational model."""

    left_hip: float
    right_hip: float
    left_wheel: float
    right_wheel: float

    def as_ordered_tuple(self) -> tuple[float, float, float, float]:
        """Return action values in the configured v1 actuator order."""

        action_values = (self.left_hip,
                         self.right_hip,
                         self.left_wheel,
                         self.right_wheel)
        return action_values


@dataclass(frozen=True)
class RobotState:
    """Reduced robot state shared by the solver, env, and visualization."""

    body_pitch_rad: float
    body_pitch_rad_s: float
    body_x_m: float
    body_x_m_s: float
    body_z_m: float
    body_z_m_s: float
    left_hip_rad: float
    left_hip_rad_s: float
    right_hip_rad: float
    right_hip_rad_s: float
    left_wheel_rad: float
    left_wheel_rad_s: float
    right_wheel_rad: float
    right_wheel_rad_s: float
    previous_action: RobotAction
    left_contact: bool
    right_contact: bool

    def as_reduced_q(self,
                     mechanism_config: RobotMechanismConfig) -> tuple[float, ...]:
        """Return reduced coordinates in the mechanism-config order."""

        coordinate_values = {
            "body_pitch_rad": self.body_pitch_rad,
            "body_x_m": self.body_x_m,
            "body_z_m": self.body_z_m,
            "left_hip_rad": self.left_hip_rad,
            "right_hip_rad": self.right_hip_rad,
            "left_wheel_rad": self.left_wheel_rad,
            "right_wheel_rad": self.right_wheel_rad,
        }
        reduced_q = tuple(coordinate_values[name]
                          for name in mechanism_config.reduced_q_order)
        mechanism_config.validate_reduced_vector("q", reduced_q)
        return reduced_q

    def as_reduced_qdot(self,
                        mechanism_config: RobotMechanismConfig) -> tuple[float, ...]:
        """Return reduced velocities in the mechanism-config order."""

        velocity_values = {
            "body_pitch_rad_s": self.body_pitch_rad_s,
            "body_x_m_s": self.body_x_m_s,
            "body_z_m_s": self.body_z_m_s,
            "left_hip_rad_s": self.left_hip_rad_s,
            "right_hip_rad_s": self.right_hip_rad_s,
            "left_wheel_rad_s": self.left_wheel_rad_s,
            "right_wheel_rad_s": self.right_wheel_rad_s,
        }
        reduced_qdot = tuple(velocity_values[name]
                             for name in mechanism_config.reduced_qdot_order)
        mechanism_config.validate_reduced_vector("qdot", reduced_qdot)
        return reduced_qdot

    def contact_flags(self) -> dict[str, bool]:
        """Return per-side ground contact flags."""

        flags = {"left": self.left_contact, "right": self.right_contact}
        return flags
