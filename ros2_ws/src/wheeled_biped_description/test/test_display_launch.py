"""Headless launch smoke test for the ROS 2 display vertical (RVT-1).

Run by the ROS `launch_test` runner (registered via `add_launch_test` in CMakeLists),
not plain pytest. Requires a ROS env and the package's `display.launch.py` (RV-1)
exposing the `gui` and `rviz` toggles. Launches headless (gui:=false, rviz:=false) and
asserts the node graph + expected topics come up. Fails until RV-1 provides the launch.
"""
import os
import time
import unittest

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
import launch_testing.actions
import pytest
import rclpy

EXPECTED_TOPICS = {"/robot_description", "/joint_states", "/tf"}


@pytest.mark.launch_test
def generate_test_description():
    pkg_share = get_package_share_directory("wheeled_biped_description")
    display_launch = os.path.join(pkg_share, "launch", "display.launch.py")
    include = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(display_launch),
        launch_arguments={"gui": "false", "rviz": "false"}.items())
    description = LaunchDescription([include, launch_testing.actions.ReadyToTest()])
    return description


class TestDisplayBringup(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        rclpy.init()
        cls.node = rclpy.create_node("rvt_display_smoke_test")

    @classmethod
    def tearDownClass(cls):
        cls.node.destroy_node()
        rclpy.shutdown()

    def test_expected_topics_present(self):
        deadline = time.time() + 15.0
        seen_topics = set()
        while time.time() < deadline and not EXPECTED_TOPICS <= seen_topics:
            rclpy.spin_once(self.node, timeout_sec=0.5)
            seen_topics = {name for name, _ in self.node.get_topic_names_and_types()}
        missing = EXPECTED_TOPICS - seen_topics
        self.assertFalse(missing, f"missing topics after bringup: {missing}")
