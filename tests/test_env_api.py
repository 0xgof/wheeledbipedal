import numpy as np

from wheeled_biped_rl.envs.wheeled_biped_env import WheeledBipedEnv


def test_wheeled_biped_env_reset_is_reproducible_and_matches_space() -> None:
    env = WheeledBipedEnv(max_episode_steps=5)

    first_observation, first_info = env.reset(seed=123)
    second_observation, second_info = env.reset(seed=123)

    assert env.observation_space.contains(first_observation)
    assert env.observation_space.contains(second_observation)
    assert np.array_equal(first_observation, second_observation)
    assert first_info["reset_reason"] == "seeded_reset"
    assert second_info["episode_step"] == 0


def test_wheeled_biped_env_step_returns_gymnasium_tuple_and_reward_components() -> None:
    env = WheeledBipedEnv(max_episode_steps=5)
    env.reset(seed=123)

    observation, reward, terminated, truncated, info = env.step(
        np.array([0.2, -0.2, 0.5, -0.5], dtype=np.float32))

    assert env.observation_space.contains(observation)
    assert isinstance(reward, float)
    assert terminated is False
    assert truncated is False
    assert info["episode_step"] == 1
    assert info["previous_action"] == {
        "left_hip": 0.314,
        "right_hip": -0.314,
        "left_wheel": 1.0,
        "right_wheel": -1.0,
    }
    assert "reward_components" in info
    assert "alive" in info["reward_components"]


def test_wheeled_biped_env_truncates_at_episode_timeout() -> None:
    env = WheeledBipedEnv(max_episode_steps=1)
    env.reset(seed=123)

    _, _, terminated, truncated, info = env.step(
        np.zeros(env.action_space.shape, dtype=np.float32))

    assert terminated is False
    assert truncated is True
    assert info["termination_reason"] == "timeout"


def test_environment_modules_do_not_import_ros() -> None:
    env = WheeledBipedEnv()

    assert "rclpy" not in type(env).__module__
