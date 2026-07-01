import math

from wheeled_biped_rl.simulation.mechanism_config import (
    load_kollarcik_2021_rigid_config,
)
from wheeled_biped_rl.simulation.robot_state import RobotAction
from wheeled_biped_rl.simulation.simple_dynamics import (
    SimpleDynamics,
    make_nominal_state,
)


def test_zero_action_rollout_stays_finite_and_deterministic() -> None:
    config = load_kollarcik_2021_rigid_config("configs/robot/wheeled_biped.yaml")
    dynamics = SimpleDynamics(config)
    initial_state = make_nominal_state(config)
    zero_action = RobotAction(0.0, 0.0, 0.0, 0.0)

    first_state = dynamics.step(initial_state, zero_action, dt_s=0.02).state
    second_state = dynamics.step(initial_state, zero_action, dt_s=0.02).state

    assert first_state == second_state
    assert all(math.isfinite(value)
               for value in first_state.as_reduced_q(config))
    assert all(math.isfinite(value)
               for value in first_state.as_reduced_qdot(config))


def test_wheel_command_increases_forward_velocity() -> None:
    config = load_kollarcik_2021_rigid_config("configs/robot/wheeled_biped.yaml")
    dynamics = SimpleDynamics(config)
    initial_state = make_nominal_state(config)
    forward_action = RobotAction(0.0, 0.0, 1.0, 1.0)

    next_state = dynamics.step(initial_state, forward_action, dt_s=0.02).state

    assert next_state.body_x_m_s > initial_state.body_x_m_s


def test_corrective_wheel_command_reduces_pitch_rate() -> None:
    config = load_kollarcik_2021_rigid_config("configs/robot/wheeled_biped.yaml")
    dynamics = SimpleDynamics(config)
    tilted_state = make_nominal_state(config, body_pitch_rad=0.2,
                                      body_pitch_rad_s=0.5)
    corrective_action = RobotAction(0.0, 0.0, -1.0, 1.0)

    next_state = dynamics.step(tilted_state, corrective_action, dt_s=0.02).state

    assert abs(next_state.body_pitch_rad_s) < abs(tilted_state.body_pitch_rad_s)


def test_hip_commands_change_effective_body_height() -> None:
    config = load_kollarcik_2021_rigid_config("configs/robot/wheeled_biped.yaml")
    dynamics = SimpleDynamics(config)
    initial_state = make_nominal_state(config)
    crouch_action = RobotAction(0.5, 0.5, 0.0, 0.0)

    next_state = dynamics.step(initial_state, crouch_action, dt_s=0.02).state

    assert next_state.body_z_m < initial_state.body_z_m
