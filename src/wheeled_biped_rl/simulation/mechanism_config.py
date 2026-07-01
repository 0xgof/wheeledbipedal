"""Mechanism configuration for reduced-order solver consumers.

The physical robot YAML stores dimensions, masses, limits, and reference metadata.
This module resolves those physical values plus a named modeling choice into the
stable coordinate/action/diagnostic contract consumed by the Layer 1 ODE/DOF solver.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

DEFAULT_REDUCED_Q_ORDER = (
    "body_pitch_rad",
    "body_x_m",
    "body_z_m",
    "left_hip_rad",
    "right_hip_rad",
    "left_wheel_rad",
    "right_wheel_rad",
)

DEFAULT_REDUCED_QDOT_ORDER = (
    "body_pitch_rad_s",
    "body_x_m_s",
    "body_z_m_s",
    "left_hip_rad_s",
    "right_hip_rad_s",
    "left_wheel_rad_s",
    "right_wheel_rad_s",
)

DEFAULT_ACTION_ORDER = (
    "left_hip",
    "right_hip",
    "left_wheel",
    "right_wheel",
)

DEFAULT_DIAGNOSTIC_FIELDS = (
    "position_residual_m",
    "velocity_residual_m_s",
    "limit_violation",
    "jacobian_condition_number",
)

DEFAULT_ACTOR_OBSERVATION_FIELDS = (
    "motor_positions",
    "motor_velocities",
    "motor_torques",
    "imu_pitch",
    "imu_roll",
    "imu_rates",
)

DEFAULT_PRIVILEGED_OBSERVATION_FIELDS = (
    "full_linkage_state",
    "exact_body_velocity",
    "contact_forces",
    "constraint_residuals",
)


@dataclass(frozen=True)
class MechanismGeometry:
    """Geometry values required by the first rigid reduced linkage model."""

    body_size_x_m: float
    body_size_y_m: float
    body_size_z_m: float
    hip_offset_x_m: float
    hip_offset_z_m: float
    track_width_m: float
    wheel_radius_m: float
    wheel_width_m: float
    link_l1_m: float
    link_l2_m: float
    link_l3_m: float
    link_l4_m: float
    link_l23_m: float

    @property
    def rigid_leg_length_m(self) -> float:
        """Return the v1 rigid no-spring effective leg length."""

        leg_length_m = self.link_l1_m + self.link_l3_m
        return leg_length_m


@dataclass(frozen=True)
class MechanismActuators:
    """Actuator limits and command modes for the reduced model."""

    hip_max_torque_nm: float
    hip_max_velocity_rad_s: float
    hip_gear_ratio: float
    wheel_max_torque_nm: float
    wheel_max_velocity_rad_s: float
    wheel_slip_torque_nm: float
    joint_damping_nm_s_rad: float


@dataclass(frozen=True)
class RobotMechanismConfig:
    """Resolved mechanism-model interpretation of the physical robot YAML."""

    mechanism_id: str
    robot_config_id: str
    topology: str
    model_level: str
    source_reference: str
    spring_enabled: bool
    contact_model: str
    constraint_model: str
    reduced_model_version: str
    hip_mode: str
    wheel_mode: str
    reduced_q_order: tuple[str, ...]
    reduced_qdot_order: tuple[str, ...]
    action_order: tuple[str, ...]
    diagnostic_fields: tuple[str, ...]
    actor_observation_fields: tuple[str, ...]
    privileged_observation_fields: tuple[str, ...]
    geometry: MechanismGeometry
    actuators: MechanismActuators
    hip_limit_lower_rad: float
    hip_limit_upper_rad: float

    def validate_reduced_vector(self,
                                vector_name: str,
                                vector_values: tuple[float, ...]) -> None:
        """Validate that a vector matches the configured reduced-coordinate shape."""

        if vector_name == "q":
            expected_length = len(self.reduced_q_order)
        elif vector_name == "qdot":
            expected_length = len(self.reduced_qdot_order)
        elif vector_name == "u":
            expected_length = len(self.action_order)
        else:
            raise ValueError(f"unknown vector name: {vector_name}")

        if len(vector_values) != expected_length:
            raise ValueError(f"{vector_name} must have length {expected_length}")


def load_kollarcik_2021_rigid_config(robot_yaml_path: str | Path) -> RobotMechanismConfig:
    """Resolve the thesis-derived rigid v1 mechanism config from robot YAML.

    Args:
        robot_yaml_path: Path to ``configs/robot/wheeled_biped.yaml``.

    Returns:
        Resolved ``RobotMechanismConfig`` for the first reduced-order solver.
    """

    robot_config = _read_yaml_mapping(Path(robot_yaml_path))
    geometry = _geometry_from_robot_config(robot_config)
    actuators = _actuators_from_robot_config(robot_config)
    joints = robot_config["joints"]
    meta = robot_config["meta"]

    mechanism_config = RobotMechanismConfig(
        mechanism_id="kollarcik_2021_rigid_v1",
        robot_config_id="robot_config_wheeled_biped_v1",
        topology="ascento_class_closed_chain",
        model_level="reduced_order",
        source_reference=meta["reference"],
        spring_enabled=False,
        contact_model="fixed_ground_contact_v1",
        constraint_model="rigid_reduced_closed_chain_v1",
        reduced_model_version="reduced_ode_v1",
        hip_mode="position_target",
        wheel_mode="torque",
        reduced_q_order=DEFAULT_REDUCED_Q_ORDER,
        reduced_qdot_order=DEFAULT_REDUCED_QDOT_ORDER,
        action_order=DEFAULT_ACTION_ORDER,
        diagnostic_fields=DEFAULT_DIAGNOSTIC_FIELDS,
        actor_observation_fields=DEFAULT_ACTOR_OBSERVATION_FIELDS,
        privileged_observation_fields=DEFAULT_PRIVILEGED_OBSERVATION_FIELDS,
        geometry=geometry,
        actuators=actuators,
        hip_limit_lower_rad=float(joints["hip"]["limit_lower_rad"]),
        hip_limit_upper_rad=float(joints["hip"]["limit_upper_rad"]))
    return mechanism_config


def _read_yaml_mapping(yaml_path: Path) -> dict[str, Any]:
    """Read a YAML file and require a top-level mapping."""

    yaml_record = yaml.safe_load(yaml_path.read_text(encoding="utf-8"))
    if not isinstance(yaml_record, dict):
        raise ValueError(f"{yaml_path} must contain a YAML mapping")
    return yaml_record


def _geometry_from_robot_config(robot_config: dict[str, Any]) -> MechanismGeometry:
    """Extract geometry and thesis loop-link defaults from robot YAML."""

    geometry = robot_config["geometry"]
    body = geometry["body"]
    body_size = body["size_m"]
    hip_offset = geometry["hip_offset_m"]
    thigh = geometry["thigh"]
    shank = geometry["shank"]
    wheel = geometry["wheel"]

    mechanism_geometry = MechanismGeometry(
        body_size_x_m=float(body_size["x"]),
        body_size_y_m=float(body_size["y"]),
        body_size_z_m=float(body_size["z"]),
        hip_offset_x_m=float(hip_offset["x"]),
        hip_offset_z_m=float(hip_offset["z"]),
        track_width_m=float(geometry["track_width_m"]),
        wheel_radius_m=float(wheel["radius_m"]),
        wheel_width_m=float(wheel["width_m"]),
        link_l1_m=float(thigh["length_m"]),
        link_l2_m=0.188,
        link_l3_m=float(shank["length_m"]),
        link_l4_m=0.093,
        link_l23_m=0.050)
    return mechanism_geometry


def _actuators_from_robot_config(robot_config: dict[str, Any]) -> MechanismActuators:
    """Extract actuator and damping values from robot YAML."""

    actuators = robot_config["actuators"]
    hip_motor = actuators["hip_motor"]
    wheel_motor = actuators["wheel_motor"]

    mechanism_actuators = MechanismActuators(
        hip_max_torque_nm=float(hip_motor["max_torque_nm"]),
        hip_max_velocity_rad_s=float(hip_motor["max_velocity_rad_s"]),
        hip_gear_ratio=float(hip_motor["gear_ratio"]),
        wheel_max_torque_nm=float(wheel_motor["max_torque_nm"]),
        wheel_max_velocity_rad_s=float(wheel_motor["max_velocity_rad_s"]),
        wheel_slip_torque_nm=float(wheel_motor["slip_torque_nm"]),
        joint_damping_nm_s_rad=float(actuators["joint_damping_nm_s_rad"]))
    return mechanism_actuators
