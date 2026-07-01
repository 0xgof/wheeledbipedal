import numpy as np

from wheeled_biped_rl.backends.python_sim_backend import PythonSimBackend
from wheeled_biped_rl.envs.wheeled_biped_env import WheeledBipedEnv
from wheeled_biped_rl.simulation.mechanism_config import (
    load_kollarcik_2021_rigid_config,
)
from wheeled_biped_rl.simulation.robot_state import RobotAction


def test_python_backend_uses_simple_dynamics() -> None:
    config = load_kollarcik_2021_rigid_config("configs/robot/wheeled_biped.yaml")
    backend = PythonSimBackend(config)
    backend.reset(seed=1)

    transition = backend.step(RobotAction(0.0, 0.0, 1.0, 1.0), dt_s=0.02)

    assert transition.state.body_x_m_s > 0.0
    assert transition.diagnostics["backend"] == "simple_dynamics"


def test_environment_terminates_unsafe_pitch_from_backend_state() -> None:
    env = WheeledBipedEnv(max_episode_steps=10)
    env.reset(seed=1)
    env.backend.state = env.backend.state.__class__(
        **{**env.backend.state.__dict__, "body_pitch_rad": 0.8})

    _, _, terminated, truncated, info = env.step(
        np.zeros(env.action_space.shape, dtype=np.float32))

    assert terminated is True
    assert truncated is False
    assert info["termination_reason"] == "fall_pitch"


def test_clipped_random_actions_remain_finite_for_short_rollout() -> None:
    env = WheeledBipedEnv(max_episode_steps=100)
    observation, _ = env.reset(seed=1)
    rng = np.random.default_rng(123)

    for _ in range(50):
        action = rng.uniform(-3.0, 3.0, size=env.action_space.shape).astype(np.float32)
        observation, _, terminated, truncated, _ = env.step(action)
        assert np.all(np.isfinite(observation))
        if terminated or truncated:
            break
