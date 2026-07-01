"""Adapters from solver state to backend-neutral visualization state."""

from __future__ import annotations

from wheeled_biped_rl.envs.leg_kinematics import LegGeometry, RigidLegKinematics
from wheeled_biped_rl.simulation.mechanism_config import RobotMechanismConfig
from wheeled_biped_rl.simulation.robot_state import RobotState
from wheeled_biped_rl.visualization.render_state import (
    BodyRenderState,
    DiagnosticsRenderState,
    LegRenderState,
    RenderState,
    WheelRenderState,
)


def render_state_from_robot_state(robot_state: RobotState,
                                  mechanism_config: RobotMechanismConfig,
                                  kinematics: RigidLegKinematics,
                                  step: int,
                                  time_s: float) -> RenderState:
    """Convert reduced solver state into a backend-neutral render state."""

    left_leg = kinematics.forward_side(
        hip_angle_rad=robot_state.left_hip_rad,
        hip_velocity_rad_s=robot_state.left_hip_rad_s,
        side="left")
    right_leg = kinematics.forward_side(
        hip_angle_rad=robot_state.right_hip_rad,
        hip_velocity_rad_s=robot_state.right_hip_rad_s,
        side="right")
    diagnostics = kinematics.diagnostics(left_leg=left_leg, right_leg=right_leg)
    geometry = mechanism_config.geometry
    body = BodyRenderState(x_m=robot_state.body_x_m,
                           z_m=robot_state.body_z_m,
                           pitch_rad=robot_state.body_pitch_rad,
                           size_x_m=geometry.body_size_x_m,
                           size_y_m=geometry.body_size_y_m,
                           size_z_m=geometry.body_size_z_m)
    left_render_leg = _leg_render_state(robot_state=robot_state,
                                        leg_geometry=left_leg,
                                        contact=robot_state.left_contact)
    right_render_leg = _leg_render_state(robot_state=robot_state,
                                         leg_geometry=right_leg,
                                         contact=robot_state.right_contact)
    left_wheel = _wheel_render_state(robot_state=robot_state,
                                     leg_render_state=left_render_leg,
                                     mechanism_config=mechanism_config,
                                     side="left")
    right_wheel = _wheel_render_state(robot_state=robot_state,
                                      leg_render_state=right_render_leg,
                                      mechanism_config=mechanism_config,
                                      side="right")
    diagnostics_state = DiagnosticsRenderState(
        max_position_residual_m=diagnostics.max_position_residual_m,
        max_velocity_residual_m_s=diagnostics.max_velocity_residual_m_s,
        within_limits=diagnostics.within_limits,
        jacobian_condition_number=diagnostics.jacobian_condition_number)
    render_state = RenderState(step=step,
                               time_s=time_s,
                               body=body,
                               left_wheel=left_wheel,
                               right_wheel=right_wheel,
                               left_leg=left_render_leg,
                               right_leg=right_render_leg,
                               diagnostics=diagnostics_state)
    return render_state


def _leg_render_state(robot_state: RobotState,
                      leg_geometry: LegGeometry,
                      contact: bool) -> LegRenderState:
    """Convert one leg geometry record into render state."""

    hip_x_m = robot_state.body_x_m
    hip_z_m = robot_state.body_z_m
    contact_x_m = hip_x_m + leg_geometry.contact_point.x_m
    contact_z_m = hip_z_m + leg_geometry.contact_point.z_m
    render_leg = LegRenderState(side=leg_geometry.side,
                                hip_angle_rad=leg_geometry.hip_angle_rad,
                                knee_angle_rad=leg_geometry.knee_angle_rad,
                                leg_length_m=leg_geometry.leg_length_m,
                                hip_x_m=hip_x_m,
                                hip_z_m=hip_z_m,
                                contact_x_m=contact_x_m,
                                contact_z_m=contact_z_m,
                                contact=contact)
    return render_leg


def _wheel_render_state(robot_state: RobotState,
                        leg_render_state: LegRenderState,
                        mechanism_config: RobotMechanismConfig,
                        side: str) -> WheelRenderState:
    """Convert one side of robot state into renderable wheel state."""

    if side == "left":
        wheel_angle_rad = robot_state.left_wheel_rad
        wheel_velocity_rad_s = robot_state.left_wheel_rad_s
        contact = robot_state.left_contact
    elif side == "right":
        wheel_angle_rad = robot_state.right_wheel_rad
        wheel_velocity_rad_s = robot_state.right_wheel_rad_s
        contact = robot_state.right_contact
    else:
        raise ValueError("side must be 'left' or 'right'")

    geometry = mechanism_config.geometry
    wheel_state = WheelRenderState(side=side,
                                   x_m=leg_render_state.contact_x_m,
                                   z_m=leg_render_state.contact_z_m,
                                   radius_m=geometry.wheel_radius_m,
                                   width_m=geometry.wheel_width_m,
                                   angle_rad=wheel_angle_rad,
                                   angular_velocity_rad_s=wheel_velocity_rad_s,
                                   contact=contact)
    return wheel_state
