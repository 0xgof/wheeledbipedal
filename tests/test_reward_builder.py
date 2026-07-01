from wheeled_biped_rl.envs.reward_builder import RewardBuilder
from wheeled_biped_rl.simulation.robot_state import RobotAction, RobotState


def make_state(pitch_rad: float,
               action: RobotAction) -> RobotState:
    state = RobotState(body_pitch_rad=pitch_rad,
                       body_pitch_rad_s=0.0,
                       body_x_m=0.0,
                       body_x_m_s=0.0,
                       body_z_m=0.4,
                       body_z_m_s=0.0,
                       left_hip_rad=0.0,
                       left_hip_rad_s=0.0,
                       right_hip_rad=0.0,
                       right_hip_rad_s=0.0,
                       left_wheel_rad=0.0,
                       left_wheel_rad_s=0.0,
                       right_wheel_rad=0.0,
                       right_wheel_rad_s=0.0,
                       previous_action=action,
                       left_contact=True,
                       right_contact=True)
    return state


def test_reward_builder_exposes_components_and_penalizes_tilt() -> None:
    builder = RewardBuilder()
    standing_state = make_state(0.0, RobotAction(0.0, 0.0, 0.0, 0.0))
    tilted_state = make_state(0.5, RobotAction(0.0, 0.0, 0.0, 0.0))

    standing_reward = builder.calculate(standing_state)
    tilted_reward = builder.calculate(tilted_state)

    assert "alive" in standing_reward.components
    assert "pitch_penalty" in standing_reward.components
    assert tilted_reward.total < standing_reward.total


def test_reward_builder_penalizes_large_previous_action() -> None:
    builder = RewardBuilder()
    quiet_state = make_state(0.0, RobotAction(0.0, 0.0, 0.0, 0.0))
    aggressive_state = make_state(0.0, RobotAction(1.0, -1.0, 1.0, -1.0))

    quiet_reward = builder.calculate(quiet_state)
    aggressive_reward = builder.calculate(aggressive_state)

    assert aggressive_reward.total < quiet_reward.total
    assert aggressive_reward.components["action_penalty"] < 0.0
