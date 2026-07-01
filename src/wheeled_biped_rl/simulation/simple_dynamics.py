"""Simple reduced dynamics for foundational Layer 1 training.

The model is deliberately low fidelity: it gives the Gymnasium environment
deterministic, finite state evolution with plausible control couplings before
the project moves to a richer solver or simulator.
"""

from __future__ import annotations

from dataclasses import dataclass
import math
import random

from wheeled_biped_rl.simulation.integration import clamp, semi_implicit_euler
from wheeled_biped_rl.simulation.mechanism_config import RobotMechanismConfig
from wheeled_biped_rl.simulation.robot_state import RobotAction, RobotState


@dataclass(frozen=True)
class DynamicsStep:
    """State transition plus diagnostics from one reduced dynamics step."""

    state: RobotState
    diagnostics: dict[str, float | bool | str]


class SimpleDynamics:
    """Deterministic semi-implicit reduced dynamics model.

    The state tracks body pitch/position, hip targets, wheel spin, effective
    body height, and previous action. It is designed for fast RL formulation
    tests, not physical validation.
    """

    def __init__(self, mechanism_config: RobotMechanismConfig) -> None:
        """Create dynamics from the resolved robot mechanism configuration."""

        self.mechanism_config = mechanism_config

    def reset(self, seed: int | None = None) -> RobotState:
        """Return a deterministic near-upright initial state."""

        rng = random.Random(seed)
        body_pitch_rad = rng.uniform(-0.005, 0.005) if seed is not None else 0.0
        initial_state = make_nominal_state(self.mechanism_config,
                                           body_pitch_rad=body_pitch_rad)
        return initial_state

    def step(self,
             robot_state: RobotState,
             action: RobotAction,
             dt_s: float) -> DynamicsStep:
        """Advance one reduced dynamics step using semi-implicit Euler."""

        clipped_action = self._clip_action(action)
        left_hip_rad, left_hip_rad_s = self._integrate_hip(
            current_position=robot_state.left_hip_rad,
            target_position=clipped_action.left_hip,
            dt_s=dt_s)
        right_hip_rad, right_hip_rad_s = self._integrate_hip(
            current_position=robot_state.right_hip_rad,
            target_position=clipped_action.right_hip,
            dt_s=dt_s)
        pitch_accel_rad_s2 = self._pitch_acceleration(robot_state, clipped_action)
        body_pitch_rad, body_pitch_rad_s = semi_implicit_euler(
            position=robot_state.body_pitch_rad,
            velocity=robot_state.body_pitch_rad_s,
            acceleration=pitch_accel_rad_s2,
            dt_s=dt_s)
        forward_accel_m_s2 = self._forward_acceleration(robot_state, clipped_action)
        body_x_m, body_x_m_s = semi_implicit_euler(position=robot_state.body_x_m,
                                                  velocity=robot_state.body_x_m_s,
                                                  acceleration=forward_accel_m_s2,
                                                  dt_s=dt_s)
        left_wheel_rad, left_wheel_rad_s = self._integrate_wheel(
            wheel_rad=robot_state.left_wheel_rad,
            wheel_rad_s=robot_state.left_wheel_rad_s,
            torque_nm=clipped_action.left_wheel,
            dt_s=dt_s)
        right_wheel_rad, right_wheel_rad_s = self._integrate_wheel(
            wheel_rad=robot_state.right_wheel_rad,
            wheel_rad_s=robot_state.right_wheel_rad_s,
            torque_nm=clipped_action.right_wheel,
            dt_s=dt_s)
        body_z_m = self._body_height(left_hip_rad, right_hip_rad)
        body_z_m_s = (body_z_m - robot_state.body_z_m) / dt_s

        next_state = RobotState(
            body_pitch_rad=body_pitch_rad,
            body_pitch_rad_s=body_pitch_rad_s,
            body_x_m=body_x_m,
            body_x_m_s=body_x_m_s,
            body_z_m=body_z_m,
            body_z_m_s=body_z_m_s,
            left_hip_rad=left_hip_rad,
            left_hip_rad_s=left_hip_rad_s,
            right_hip_rad=right_hip_rad,
            right_hip_rad_s=right_hip_rad_s,
            left_wheel_rad=left_wheel_rad,
            left_wheel_rad_s=left_wheel_rad_s,
            right_wheel_rad=right_wheel_rad,
            right_wheel_rad_s=right_wheel_rad_s,
            previous_action=clipped_action,
            left_contact=True,
            right_contact=True)
        diagnostics = {
            "backend": "simple_dynamics",
            "dt_s": dt_s,
            "pitch_accel_rad_s2": pitch_accel_rad_s2,
            "forward_accel_m_s2": forward_accel_m_s2,
            "left_contact": True,
            "right_contact": True,
        }
        dynamics_step = DynamicsStep(state=next_state, diagnostics=diagnostics)
        return dynamics_step

    def _clip_action(self, action: RobotAction) -> RobotAction:
        """Clip actuator commands to configured limits."""

        hip_lower = self.mechanism_config.hip_limit_lower_rad
        hip_upper = self.mechanism_config.hip_limit_upper_rad
        wheel_limit = self.mechanism_config.actuators.wheel_max_torque_nm
        clipped_action = RobotAction(
            left_hip=clamp(action.left_hip, hip_lower, hip_upper),
            right_hip=clamp(action.right_hip, hip_lower, hip_upper),
            left_wheel=clamp(action.left_wheel, -wheel_limit, wheel_limit),
            right_wheel=clamp(action.right_wheel, -wheel_limit, wheel_limit))
        return clipped_action

    def _integrate_hip(self,
                       current_position: float,
                       target_position: float,
                       dt_s: float) -> tuple[float, float]:
        """Move hip position toward target within velocity limits."""

        max_delta = self.mechanism_config.actuators.hip_max_velocity_rad_s * dt_s
        requested_delta = target_position - current_position
        applied_delta = clamp(requested_delta, -max_delta, max_delta)
        next_position = current_position + applied_delta
        next_velocity = applied_delta / dt_s
        integrated_hip = (next_position, next_velocity)
        return integrated_hip

    def _integrate_wheel(self,
                         wheel_rad: float,
                         wheel_rad_s: float,
                         torque_nm: float,
                         dt_s: float) -> tuple[float, float]:
        """Integrate wheel spin with torque input and viscous damping."""

        wheel_inertia = 0.02
        damping = 0.2
        wheel_accel_rad_s2 = (torque_nm / wheel_inertia) - damping * wheel_rad_s
        next_wheel_rad, next_wheel_rad_s = semi_implicit_euler(
            position=wheel_rad,
            velocity=wheel_rad_s,
            acceleration=wheel_accel_rad_s2,
            dt_s=dt_s)
        max_velocity = self.mechanism_config.actuators.wheel_max_velocity_rad_s
        next_wheel_rad_s = clamp(next_wheel_rad_s, -max_velocity, max_velocity)
        integrated_wheel = (next_wheel_rad, next_wheel_rad_s)
        return integrated_wheel

    def _pitch_acceleration(self,
                            robot_state: RobotState,
                            action: RobotAction) -> float:
        """Return simplified pitch acceleration from gravity and controls."""

        gravity_instability = 4.0 * math.sin(robot_state.body_pitch_rad)
        damping = -1.2 * robot_state.body_pitch_rad_s
        differential_wheel_recovery = -1.5 * (action.right_wheel - action.left_wheel)
        hip_posture = -0.3 * (action.left_hip + action.right_hip)
        pitch_accel_rad_s2 = (gravity_instability
                              + damping
                              + differential_wheel_recovery
                              + hip_posture)
        return pitch_accel_rad_s2

    def _forward_acceleration(self,
                              robot_state: RobotState,
                              action: RobotAction) -> float:
        """Return simplified forward acceleration from average wheel command."""

        wheel_drive = 1.2 * (action.left_wheel + action.right_wheel)
        drag = -0.4 * robot_state.body_x_m_s
        forward_accel_m_s2 = wheel_drive + drag
        return forward_accel_m_s2

    def _body_height(self,
                     left_hip_rad: float,
                     right_hip_rad: float) -> float:
        """Return effective body height from average hip posture."""

        geometry = self.mechanism_config.geometry
        average_abs_hip = 0.5 * (abs(left_hip_rad) + abs(right_hip_rad))
        leg_height_m = geometry.rigid_leg_length_m * math.cos(average_abs_hip)
        body_height_m = geometry.wheel_radius_m + max(0.05, leg_height_m)
        return body_height_m


def make_nominal_state(mechanism_config: RobotMechanismConfig,
                       body_pitch_rad: float = 0.0,
                       body_pitch_rad_s: float = 0.0) -> RobotState:
    """Create a nominal standing state for resets and tests."""

    geometry = mechanism_config.geometry
    standing_height_m = geometry.rigid_leg_length_m + geometry.wheel_radius_m
    zero_action = RobotAction(left_hip=0.0,
                              right_hip=0.0,
                              left_wheel=0.0,
                              right_wheel=0.0)
    nominal_state = RobotState(
        body_pitch_rad=body_pitch_rad,
        body_pitch_rad_s=body_pitch_rad_s,
        body_x_m=0.0,
        body_x_m_s=0.0,
        body_z_m=standing_height_m,
        body_z_m_s=0.0,
        left_hip_rad=0.0,
        left_hip_rad_s=0.0,
        right_hip_rad=0.0,
        right_hip_rad_s=0.0,
        left_wheel_rad=0.0,
        left_wheel_rad_s=0.0,
        right_wheel_rad=0.0,
        right_wheel_rad_s=0.0,
        previous_action=zero_action,
        left_contact=True,
        right_contact=True)
    return nominal_state
