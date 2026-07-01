from wheeled_biped_rl.envs.leg_kinematics import RigidLegKinematics
from wheeled_biped_rl.simulation.mechanism_config import (
    load_kollarcik_2021_rigid_config,
)
from wheeled_biped_rl.backends.python_sim_backend import PythonSimBackend
from wheeled_biped_rl.visualization.adapters import render_state_from_robot_state
from wheeled_biped_rl.visualization.frame import VisualizationFrame
from wheeled_biped_rl.visualization.plugins.rviz_sink import (
    RvizFrameMessages,
    RvizSink,
    frame_to_rviz_messages,
)


class FakeRvizPublisher:
    def __init__(self) -> None:
        self.messages = []

    def publish(self, messages: RvizFrameMessages) -> None:
        self.messages.append(messages)


def make_frame() -> VisualizationFrame:
    config = load_kollarcik_2021_rigid_config("configs/robot/wheeled_biped.yaml")
    backend = PythonSimBackend(config)
    state = backend.reset(seed=1)
    kinematics = RigidLegKinematics(config)
    render_state = render_state_from_robot_state(robot_state=state,
                                                 mechanism_config=config,
                                                 kinematics=kinematics,
                                                 step=3,
                                                 time_s=0.06)
    frame = VisualizationFrame(render_state=render_state)
    return frame


def test_rviz_sink_imports_without_ros_dependencies() -> None:
    publisher = FakeRvizPublisher()
    sink = RvizSink(publisher=publisher)

    sink.start({"run_id": "run_test"})
    sink.consume(make_frame())
    sink.close()

    assert len(publisher.messages) == 1


def test_frame_to_rviz_messages_maps_joint_states_and_tf_deterministically() -> None:
    frame = make_frame()

    messages = frame_to_rviz_messages(frame)

    assert messages.joint_state["name"] == [
        "left_hip_joint",
        "right_hip_joint",
        "left_wheel_joint",
        "right_wheel_joint",
    ]
    assert messages.tf_transforms[0]["child_frame_id"] == "base_link"
    assert messages.markers[0]["namespace"] == "contacts"
