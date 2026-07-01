from pathlib import Path

from wheeled_biped_rl.envs.leg_kinematics import RigidLegKinematics
from wheeled_biped_rl.simulation.mechanism_config import (
    load_kollarcik_2021_rigid_config,
)
from wheeled_biped_rl.simulation.robot_state import RobotAction, RobotState
from wheeled_biped_rl.visualization.adapters import render_state_from_robot_state
from wheeled_biped_rl.visualization.frame import VisualizationFrame
from wheeled_biped_rl.visualization.render_state import BodyRenderState


def make_state() -> RobotState:
    action = RobotAction(left_hip=0.1,
                         right_hip=-0.1,
                         left_wheel=0.2,
                         right_wheel=-0.2)
    state = RobotState(body_pitch_rad=0.05,
                       body_pitch_rad_s=0.1,
                       body_x_m=1.0,
                       body_x_m_s=0.2,
                       body_z_m=0.4,
                       body_z_m_s=0.0,
                       left_hip_rad=0.0,
                       left_hip_rad_s=0.0,
                       right_hip_rad=0.0,
                       right_hip_rad_s=0.0,
                       left_wheel_rad=1.5,
                       left_wheel_rad_s=2.0,
                       right_wheel_rad=1.6,
                       right_wheel_rad_s=2.1,
                       previous_action=action,
                       left_contact=True,
                       right_contact=True)
    return state


def test_render_state_converts_robot_state_to_backend_neutral_frame() -> None:
    config = load_kollarcik_2021_rigid_config(Path("configs/robot/wheeled_biped.yaml"))
    kinematics = RigidLegKinematics(config)

    render_state = render_state_from_robot_state(robot_state=make_state(),
                                                 mechanism_config=config,
                                                 kinematics=kinematics,
                                                 step=7,
                                                 time_s=0.14)

    assert isinstance(render_state.body, BodyRenderState)
    assert render_state.step == 7
    assert render_state.time_s == 0.14
    assert render_state.body.pitch_rad == 0.05
    assert render_state.left_wheel.angle_rad == 1.5
    assert render_state.right_wheel.angle_rad == 1.6
    assert render_state.left_leg.contact is True
    assert render_state.right_leg.contact is True
    assert render_state.diagnostics.within_limits is True


def test_visualization_frame_serializes_action_reward_and_diagnostics() -> None:
    config = load_kollarcik_2021_rigid_config(Path("configs/robot/wheeled_biped.yaml"))
    kinematics = RigidLegKinematics(config)
    render_state = render_state_from_robot_state(robot_state=make_state(),
                                                 mechanism_config=config,
                                                 kinematics=kinematics,
                                                 step=1,
                                                 time_s=0.02)
    frame = VisualizationFrame(render_state=render_state,
                               action=(0.1, -0.1, 0.2, -0.2),
                               reward=1.25,
                               terminated=False,
                               truncated=False,
                               metadata={"candidate_id": "cand_test"})

    frame_dict = frame.to_dict()
    loaded_frame = VisualizationFrame.from_dict(frame_dict)

    assert loaded_frame == frame
    assert frame_dict["render_state"]["step"] == 1
    assert frame_dict["action"] == [0.1, -0.1, 0.2, -0.2]
    assert frame_dict["metadata"]["candidate_id"] == "cand_test"
