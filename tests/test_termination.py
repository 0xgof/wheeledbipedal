from wheeled_biped_rl.envs.termination import TerminationChecker
from wheeled_biped_rl.simulation.robot_state import RobotAction, RobotState


def make_state(pitch_rad: float = 0.0,
               body_z_m: float = 0.4) -> RobotState:
    state = RobotState(body_pitch_rad=pitch_rad,
                       body_pitch_rad_s=0.0,
                       body_x_m=0.0,
                       body_x_m_s=0.0,
                       body_z_m=body_z_m,
                       body_z_m_s=0.0,
                       left_hip_rad=0.0,
                       left_hip_rad_s=0.0,
                       right_hip_rad=0.0,
                       right_hip_rad_s=0.0,
                       left_wheel_rad=0.0,
                       left_wheel_rad_s=0.0,
                       right_wheel_rad=0.0,
                       right_wheel_rad_s=0.0,
                       previous_action=RobotAction(0.0, 0.0, 0.0, 0.0),
                       left_contact=True,
                       right_contact=True)
    return state


def test_termination_checker_terminates_unsafe_pitch() -> None:
    checker = TerminationChecker(max_episode_steps=100)

    decision = checker.check(make_state(pitch_rad=0.9), episode_step=1)

    assert decision.terminated is True
    assert decision.truncated is False
    assert decision.reason == "fall_pitch"


def test_termination_checker_truncates_timeout_without_termination() -> None:
    checker = TerminationChecker(max_episode_steps=2)

    decision = checker.check(make_state(), episode_step=2)

    assert decision.terminated is False
    assert decision.truncated is True
    assert decision.reason == "timeout"
