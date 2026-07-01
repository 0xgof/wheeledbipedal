from pathlib import Path

from wheeled_biped_rl.simulation.mechanism_config import (
    DEFAULT_REDUCED_Q_ORDER,
    DEFAULT_REDUCED_QDOT_ORDER,
    load_kollarcik_2021_rigid_config,
)
from wheeled_biped_rl.simulation.robot_state import RobotAction, RobotState


def test_robot_action_exposes_four_actuator_channels_without_knee() -> None:
    action = RobotAction(left_hip=0.1,
                         right_hip=0.2,
                         left_wheel=0.3,
                         right_wheel=0.4)

    assert action.as_ordered_tuple() == (0.1, 0.2, 0.3, 0.4)
    assert not hasattr(action, "left_knee")
    assert not hasattr(action, "right_knee")


def test_robot_state_exports_reduced_vectors_in_config_order() -> None:
    config = load_kollarcik_2021_rigid_config(Path("configs/robot/wheeled_biped.yaml"))
    previous_action = RobotAction(left_hip=0.1,
                                  right_hip=-0.1,
                                  left_wheel=0.2,
                                  right_wheel=-0.2)
    state = RobotState(body_pitch_rad=0.01,
                       body_pitch_rad_s=0.02,
                       body_x_m=1.0,
                       body_x_m_s=2.0,
                       body_z_m=0.4,
                       body_z_m_s=-0.1,
                       left_hip_rad=0.3,
                       left_hip_rad_s=0.4,
                       right_hip_rad=-0.3,
                       right_hip_rad_s=-0.4,
                       left_wheel_rad=5.0,
                       left_wheel_rad_s=6.0,
                       right_wheel_rad=-5.0,
                       right_wheel_rad_s=-6.0,
                       previous_action=previous_action,
                       left_contact=True,
                       right_contact=False)

    reduced_q = state.as_reduced_q(config)
    reduced_qdot = state.as_reduced_qdot(config)

    assert config.reduced_q_order == DEFAULT_REDUCED_Q_ORDER
    assert config.reduced_qdot_order == DEFAULT_REDUCED_QDOT_ORDER
    assert reduced_q == (0.01, 1.0, 0.4, 0.3, -0.3, 5.0, -5.0)
    assert reduced_qdot == (0.02, 2.0, -0.1, 0.4, -0.4, 6.0, -6.0)
    assert state.contact_flags() == {"left": True, "right": False}
