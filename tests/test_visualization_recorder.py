from pathlib import Path

from wheeled_biped_rl.envs.leg_kinematics import RigidLegKinematics
from wheeled_biped_rl.simulation.mechanism_config import (
    load_kollarcik_2021_rigid_config,
)
from wheeled_biped_rl.simulation.robot_state import RobotAction, RobotState
from wheeled_biped_rl.visualization.adapters import render_state_from_robot_state
from wheeled_biped_rl.visualization.frame import VisualizationFrame
from wheeled_biped_rl.visualization.recorder import JsonlTrajectorySink
from wheeled_biped_rl.visualization.replay import load_visualization_frames
from wheeled_biped_rl.visualization.sinks import VisualizationSink


class CountingSink:
    def __init__(self) -> None:
        self.started = False
        self.frames = []
        self.closed = False

    def start(self, metadata: dict[str, object]) -> None:
        self.started = True

    def consume(self, frame: VisualizationFrame) -> None:
        self.frames.append(frame)

    def close(self) -> None:
        self.closed = True


def make_frame(step: int) -> VisualizationFrame:
    config = load_kollarcik_2021_rigid_config(Path("configs/robot/wheeled_biped.yaml"))
    kinematics = RigidLegKinematics(config)
    action = RobotAction(left_hip=0.0,
                         right_hip=0.0,
                         left_wheel=0.1,
                         right_wheel=0.1)
    state = RobotState(body_pitch_rad=0.0,
                       body_pitch_rad_s=0.0,
                       body_x_m=0.0,
                       body_x_m_s=0.0,
                       body_z_m=0.4,
                       body_z_m_s=0.0,
                       left_hip_rad=0.0,
                       left_hip_rad_s=0.0,
                       right_hip_rad=0.0,
                       right_hip_rad_s=0.0,
                       left_wheel_rad=float(step),
                       left_wheel_rad_s=0.0,
                       right_wheel_rad=float(step),
                       right_wheel_rad_s=0.0,
                       previous_action=action,
                       left_contact=True,
                       right_contact=True)
    render_state = render_state_from_robot_state(robot_state=state,
                                                 mechanism_config=config,
                                                 kinematics=kinematics,
                                                 step=step,
                                                 time_s=step * 0.02)
    frame = VisualizationFrame(render_state=render_state,
                               action=action.as_ordered_tuple(),
                               reward=float(step),
                               terminated=False,
                               truncated=False,
                               metadata={})
    return frame


def test_visualization_sink_protocol_accepts_custom_sink() -> None:
    sink: VisualizationSink = CountingSink()
    frame = make_frame(1)

    sink.start({"run_id": "run_test"})
    sink.consume(frame)
    sink.close()

    assert sink.started is True
    assert sink.frames == [frame]
    assert sink.closed is True


def test_jsonl_trajectory_sink_records_and_replays_frames(tmp_path) -> None:
    trajectory_path = tmp_path / "trajectory.jsonl"
    sink = JsonlTrajectorySink(trajectory_path)
    first_frame = make_frame(1)
    second_frame = make_frame(2)

    sink.start({"run_id": "run_test"})
    sink.consume(first_frame)
    sink.consume(second_frame)
    sink.close()

    loaded_frames = load_visualization_frames(trajectory_path)

    assert loaded_frames == [first_frame, second_frame]
    assert trajectory_path.read_text(encoding="utf-8").count("\n") == 3
