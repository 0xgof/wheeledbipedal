import numpy as np

from wheeled_biped_rl.envs.action_adapter import ActionAdapter
from wheeled_biped_rl.simulation.mechanism_config import (
    load_kollarcik_2021_rigid_config,
)


def test_action_adapter_clips_and_scales_normalized_actions() -> None:
    mechanism_config = load_kollarcik_2021_rigid_config(
        "configs/robot/wheeled_biped.yaml")
    adapter = ActionAdapter(mechanism_config)

    action = adapter.adapt(np.array([2.0, -2.0, 0.5, -0.5], dtype=np.float32))

    assert action.left_hip == mechanism_config.hip_limit_upper_rad
    assert action.right_hip == mechanism_config.hip_limit_lower_rad
    assert action.left_wheel == 1.0
    assert action.right_wheel == -1.0


def test_action_adapter_rejects_wrong_action_shape() -> None:
    mechanism_config = load_kollarcik_2021_rigid_config(
        "configs/robot/wheeled_biped.yaml")
    adapter = ActionAdapter(mechanism_config)

    try:
        adapter.adapt(np.array([0.0, 0.0], dtype=np.float32))
    except ValueError as exc:
        assert "shape" in str(exc)
    else:
        raise AssertionError("wrong action shape should fail")
