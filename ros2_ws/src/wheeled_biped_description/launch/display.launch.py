"""RViz display launch for the wheeled-biped robot (RV-1).

Brings up robot_state_publisher (URDF expanded from the Xacro), a joint-state
source, and RViz. Two toggles keep it headless-testable:
  gui:=true|false   -> joint_state_publisher_gui (sliders) vs joint_state_publisher
  rviz:=true|false  -> start RViz or not
"""
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.conditions import IfCondition, UnlessCondition
from launch.substitutions import Command, LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue
from launch_ros.substitutions import FindPackageShare


def generate_launch_description() -> LaunchDescription:
    pkg_share = FindPackageShare("wheeled_biped_description")
    xacro_path = PathJoinSubstitution([pkg_share, "urdf", "wheeled_biped.urdf.xacro"])
    rviz_config = PathJoinSubstitution([pkg_share, "rviz", "display.rviz"])

    gui = LaunchConfiguration("gui")
    rviz = LaunchConfiguration("rviz")
    robot_description = ParameterValue(Command(["xacro ", xacro_path]), value_type=str)

    robot_state_publisher = Node(package="robot_state_publisher",
                                 executable="robot_state_publisher",
                                 parameters=[{"robot_description": robot_description}])

    joint_state_gui = Node(package="joint_state_publisher_gui",
                           executable="joint_state_publisher_gui",
                           condition=IfCondition(gui))

    joint_state_headless = Node(package="joint_state_publisher",
                                executable="joint_state_publisher",
                                condition=UnlessCondition(gui))

    rviz_node = Node(package="rviz2",
                     executable="rviz2",
                     arguments=["-d", rviz_config],
                     condition=IfCondition(rviz))

    launch_description = LaunchDescription([
        DeclareLaunchArgument("gui", default_value="true"),
        DeclareLaunchArgument("rviz", default_value="true"),
        robot_state_publisher,
        joint_state_gui,
        joint_state_headless,
        rviz_node,
    ])
    return launch_description
