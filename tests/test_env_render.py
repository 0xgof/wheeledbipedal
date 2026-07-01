import numpy as np

from wheeled_biped_rl.envs.wheeled_biped_env import WheeledBipedEnv


def test_render_is_disabled_by_default() -> None:
    env = WheeledBipedEnv()
    env.reset(seed=1)

    frame = env.render()

    assert frame is None


def test_env_render_rgb_array_returns_deterministic_frame_dimensions() -> None:
    env = WheeledBipedEnv(render_mode="rgb_array")
    env.reset(seed=1)

    first_frame = env.render()
    second_frame = env.render()

    assert isinstance(first_frame, np.ndarray)
    assert first_frame.shape == (240, 320, 3)
    assert first_frame.dtype == np.uint8
    assert np.array_equal(first_frame, second_frame)


def test_env_render_uses_render_state_pipeline() -> None:
    env = WheeledBipedEnv(render_mode="rgb_array")
    env.reset(seed=1)
    env.step(np.array([0.1, -0.1, 0.2, -0.2], dtype=np.float32))

    render_state = env.render_state()
    frame = env.render()

    assert render_state.step == 1
    assert render_state.body.x_m == env.state.body_x_m
    assert frame.shape == (240, 320, 3)
