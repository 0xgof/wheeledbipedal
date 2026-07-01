from pathlib import Path

from wheeled_biped_rl.simulation.mechanism_config import (
    DEFAULT_ACTION_ORDER,
    DEFAULT_REDUCED_Q_ORDER,
    DEFAULT_REDUCED_QDOT_ORDER,
    load_kollarcik_2021_rigid_config,
)


def test_kollarcik_rigid_config_resolves_from_robot_yaml() -> None:
    robot_yaml = Path("configs/robot/wheeled_biped.yaml")

    mechanism_config = load_kollarcik_2021_rigid_config(robot_yaml)

    assert mechanism_config.mechanism_id == "kollarcik_2021_rigid_v1"
    assert mechanism_config.topology == "ascento_class_closed_chain"
    assert mechanism_config.model_level == "reduced_order"
    assert mechanism_config.spring_enabled is False
    assert mechanism_config.action_order == DEFAULT_ACTION_ORDER
    assert mechanism_config.reduced_q_order == DEFAULT_REDUCED_Q_ORDER
    assert mechanism_config.reduced_qdot_order == DEFAULT_REDUCED_QDOT_ORDER
    assert mechanism_config.geometry.wheel_radius_m == 0.07
    assert mechanism_config.geometry.link_l1_m == 0.24
    assert mechanism_config.geometry.link_l3_m == 0.193
    assert mechanism_config.actuators.wheel_slip_torque_nm == 0.5


def test_kollarcik_rigid_config_keeps_model_assumptions_versioned() -> None:
    mechanism_config = load_kollarcik_2021_rigid_config(
        Path("configs/robot/wheeled_biped.yaml"))

    assert mechanism_config.contact_model == "fixed_ground_contact_v1"
    assert mechanism_config.constraint_model == "rigid_reduced_closed_chain_v1"
    assert mechanism_config.hip_mode == "position_target"
    assert mechanism_config.wheel_mode == "torque"
    assert "motor_positions" in mechanism_config.actor_observation_fields
    assert "constraint_residuals" in mechanism_config.privileged_observation_fields
