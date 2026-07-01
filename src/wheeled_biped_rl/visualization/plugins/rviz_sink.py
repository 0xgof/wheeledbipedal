"""ROS-isolated RViz sink for replaying visualization frames.

The module exposes plain Python message dictionaries so it can be imported and
tested without ROS 2. A ROS-facing wrapper can translate these dictionaries into
real ``sensor_msgs``/``tf2``/marker messages when ROS is available.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from wheeled_biped_rl.visualization.frame import VisualizationFrame


@dataclass(frozen=True)
class RvizFrameMessages:
    """Plain message bundle equivalent to joint states, TF, and markers."""

    joint_state: dict[str, object]
    tf_transforms: list[dict[str, object]]
    markers: list[dict[str, object]]


class RvizPublisher(Protocol):
    """Publisher interface used by the RViz sink boundary."""

    def publish(self, messages: RvizFrameMessages) -> None:
        """Publish one RViz message bundle."""


class RvizSink:
    """Visualization sink that sends frames to an injected RViz publisher."""

    def __init__(self, publisher: RvizPublisher) -> None:
        """Create a sink without importing ROS modules."""

        self.publisher = publisher
        self.started = False
        self.metadata: dict[str, object] = {}

    def start(self, metadata: dict[str, object]) -> None:
        """Start a replay stream with metadata."""

        self.metadata = dict(metadata)
        self.started = True

    def consume(self, frame: VisualizationFrame) -> None:
        """Convert one frame and publish it through the injected publisher."""

        if not self.started:
            self.start({})
        messages = frame_to_rviz_messages(frame)
        self.publisher.publish(messages)

    def close(self) -> None:
        """Close the replay stream."""

        self.started = False


def frame_to_rviz_messages(frame: VisualizationFrame) -> RvizFrameMessages:
    """Convert one visualization frame to deterministic RViz message data."""

    render_state = frame.render_state
    joint_state = {
        "stamp_s": render_state.time_s,
        "name": [
            "left_hip_joint",
            "right_hip_joint",
            "left_wheel_joint",
            "right_wheel_joint",
        ],
        "position": [
            render_state.left_leg.hip_angle_rad,
            render_state.right_leg.hip_angle_rad,
            render_state.left_wheel.angle_rad,
            render_state.right_wheel.angle_rad,
        ],
        "velocity": [
            0.0,
            0.0,
            render_state.left_wheel.angular_velocity_rad_s,
            render_state.right_wheel.angular_velocity_rad_s,
        ],
    }
    tf_transforms = [
        {
            "stamp_s": render_state.time_s,
            "frame_id": "world",
            "child_frame_id": "base_link",
            "translation": {
                "x": render_state.body.x_m,
                "y": 0.0,
                "z": render_state.body.z_m,
            },
            "rotation_rpy": {
                "roll": 0.0,
                "pitch": render_state.body.pitch_rad,
                "yaw": 0.0,
            },
        }
    ]
    markers = _contact_markers(frame)
    messages = RvizFrameMessages(joint_state=joint_state,
                                 tf_transforms=tf_transforms,
                                 markers=markers)
    return messages


def _contact_markers(frame: VisualizationFrame) -> list[dict[str, object]]:
    """Create deterministic contact markers from render-state contacts."""

    render_state = frame.render_state
    markers = []
    for marker_id, wheel in enumerate(
            [render_state.left_wheel, render_state.right_wheel]):
        marker = {
            "namespace": "contacts",
            "id": marker_id,
            "frame_id": "world",
            "type": "sphere",
            "position": {"x": wheel.x_m, "y": 0.0, "z": wheel.z_m},
            "scale": 0.04 if wheel.contact else 0.02,
            "color": "green" if wheel.contact else "gray",
        }
        markers.append(marker)
    diagnostic_marker = {
        "namespace": "diagnostics",
        "id": 100,
        "frame_id": "world",
        "type": "text",
        "text": (
            "residual="
            f"{render_state.diagnostics.max_position_residual_m:.6f}"
        ),
        "position": {
            "x": render_state.body.x_m,
            "y": 0.0,
            "z": render_state.body.z_m + 0.2,
        },
    }
    markers.append(diagnostic_marker)
    return markers
