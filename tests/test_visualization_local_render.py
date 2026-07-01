import numpy as np

from wheeled_biped_rl.envs.leg_kinematics import RigidLegKinematics
from wheeled_biped_rl.simulation.mechanism_config import (
    load_kollarcik_2021_rigid_config,
)
from wheeled_biped_rl.backends.python_sim_backend import PythonSimBackend
from wheeled_biped_rl.visualization.adapters import render_state_from_robot_state
from wheeled_biped_rl.visualization.plugins.gym_render_sink import (
    RgbArrayRenderer,
    render_rollout_frames,
)


def test_rgb_array_renderer_consumes_render_state_without_viewer_dependency() -> None:
    config = load_kollarcik_2021_rigid_config("configs/robot/wheeled_biped.yaml")
    backend = PythonSimBackend(config)
    state = backend.reset(seed=1)
    kinematics = RigidLegKinematics(config)
    render_state = render_state_from_robot_state(robot_state=state,
                                                 mechanism_config=config,
                                                 kinematics=kinematics,
                                                 step=0,
                                                 time_s=0.0)
    renderer = RgbArrayRenderer(width_px=160, height_px=120)

    rgb_array = renderer.render(render_state)

    assert rgb_array.shape == (120, 160, 3)
    assert rgb_array.dtype == np.uint8
    assert rgb_array.max() > rgb_array.min()


def test_render_rollout_frames_has_deterministic_shape() -> None:
    env = PythonSimBackend(
        load_kollarcik_2021_rigid_config("configs/robot/wheeled_biped.yaml"))
    state = env.reset(seed=1)
    config = env.mechanism_config
    kinematics = RigidLegKinematics(config)
    render_state = render_state_from_robot_state(robot_state=state,
                                                 mechanism_config=config,
                                                 kinematics=kinematics,
                                                 step=0,
                                                 time_s=0.0)

    frames = render_rollout_frames([render_state], width_px=80, height_px=60)

    assert len(frames) == 1
    assert frames[0].shape == (60, 80, 3)
