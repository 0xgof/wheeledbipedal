import numpy as np

from wheeled_biped_rl.envs.observation_builder import ObservationBuilder
from wheeled_biped_rl.simulation.mechanism_config import (
    load_kollarcik_2021_rigid_config,
)
from wheeled_biped_rl.simulation.robot_state import RobotAction, RobotState


def make_state() -> RobotState:
    state = RobotState(body_pitch_rad=0.1,
                       body_pitch_rad_s=0.2,
                       body_x_m=1.0,
                       body_x_m_s=0.3,
                       body_z_m=0.4,
                       body_z_m_s=-0.1,
                       left_hip_rad=0.2,
                       left_hip_rad_s=0.3,
                       right_hip_rad=-0.2,
                       right_hip_rad_s=-0.3,
                       left_wheel_rad=0.4,
                       left_wheel_rad_s=0.5,
                       right_wheel_rad=-0.4,
                       right_wheel_rad_s=-0.5,
                       previous_action=RobotAction(0.1, -0.1, 0.2, -0.2),
                       left_contact=True,
                       right_contact=True)
    return state


def test_observation_builder_returns_actor_observation_vector() -> None:
    mechanism_config = load_kollarcik_2021_rigid_config(
        "configs/robot/wheeled_biped.yaml")
    builder = ObservationBuilder(mechanism_config)

    observation = builder.build(make_state())

    assert observation.shape == builder.space.shape
    assert observation.dtype == np.float32
    assert np.all(np.isfinite(observation))
    assert np.isclose(observation[0], 0.2)
    assert np.isclose(observation[4], 0.3)
    assert np.isclose(observation[8], 0.1)
    assert np.isclose(observation[12], 0.1)
