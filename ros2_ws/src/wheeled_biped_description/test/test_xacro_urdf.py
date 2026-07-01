"""URDF / Xacro tests for the ROS 2 display vertical (RVT-1).

Requires a ROS env (`xacro`, `check_urdf` on PATH); tests skip if those tools are absent.
These specify the description RD-1 must produce: structure, joint types, pitch axes,
left/right mirroring, and config-driven geometry. Tests-first — they fail until RD-1
authors the Xacro and BRG-2 wires the config load.
"""
import shutil
import subprocess
import xml.etree.ElementTree as ET
from pathlib import Path

import pytest
import yaml

REPO_ROOT = Path(__file__).resolve().parents[4]
PKG_DIR = Path(__file__).resolve().parents[1]
XACRO_PATH = PKG_DIR / "urdf" / "wheeled_biped.urdf.xacro"
CONFIG_PATH = REPO_ROOT / "configs" / "robot" / "wheeled_biped.yaml"

PITCH_AXIS = (0.0, 1.0, 0.0)
EXPECTED_LINKS = {
    "base_link",
    "left_thigh", "left_shank", "left_wheel",
    "right_thigh", "right_shank", "right_wheel",
}
EXPECTED_JOINTS = {
    "left_hip_joint", "left_knee_joint", "left_wheel_joint",
    "right_hip_joint", "right_knee_joint", "right_wheel_joint",
}
REVOLUTE_JOINTS = ("left_hip_joint", "left_knee_joint",
                   "right_hip_joint", "right_knee_joint")
CONTINUOUS_JOINTS = ("left_wheel_joint", "right_wheel_joint")

requires_xacro = pytest.mark.skipif(shutil.which("xacro") is None,
                                    reason="xacro not on PATH (needs ROS env)")
requires_check_urdf = pytest.mark.skipif(shutil.which("check_urdf") is None,
                                         reason="check_urdf not on PATH (needs ROS env)")


def expand_xacro(xacro_path: Path) -> str:
    completed = subprocess.run(["xacro", str(xacro_path)],
                               capture_output=True, text=True, check=True)
    return completed.stdout


def find_joint(root: ET.Element,
               joint_name: str) -> ET.Element:
    for joint in root.findall("joint"):
        if joint.get("name") == joint_name:
            return joint
    raise AssertionError(f"joint not found in URDF: {joint_name}")


def joint_origin_y(root: ET.Element,
                   joint_name: str) -> float:
    joint = find_joint(root, joint_name)
    xyz = joint.find("origin").get("xyz").split()
    origin_y = float(xyz[1])
    return origin_y


def joint_axis(root: ET.Element,
               joint_name: str) -> tuple:
    joint = find_joint(root, joint_name)
    axis_components = tuple(float(value)
                            for value in joint.find("axis").get("xyz").split())
    return axis_components


def link_cylinder_length(root: ET.Element,
                         link_name: str) -> float:
    for link in root.findall("link"):
        if link.get("name") == link_name:
            cylinder = link.find("visual/geometry/cylinder")
            cylinder_length = float(cylinder.get("length"))
            return cylinder_length
    raise AssertionError(f"link not found in URDF: {link_name}")


@pytest.fixture
def urdf_root() -> ET.Element:
    root = ET.fromstring(expand_xacro(XACRO_PATH))
    return root


@requires_xacro
def test_xacro_expands_to_xml() -> None:
    urdf_xml = expand_xacro(XACRO_PATH)

    assert urdf_xml.strip().startswith("<")


@requires_xacro
def test_urdf_has_expected_links_and_joints(urdf_root) -> None:
    link_names = {link.get("name") for link in urdf_root.findall("link")}
    joint_names = {joint.get("name") for joint in urdf_root.findall("joint")}

    assert link_names == EXPECTED_LINKS
    assert joint_names == EXPECTED_JOINTS


@requires_xacro
def test_leg_joints_are_revolute_and_wheels_continuous(urdf_root) -> None:
    types = {joint.get("name"): joint.get("type")
             for joint in urdf_root.findall("joint")}

    for revolute in REVOLUTE_JOINTS:
        assert types[revolute] == "revolute"
    for continuous in CONTINUOUS_JOINTS:
        assert types[continuous] == "continuous"


@requires_xacro
def test_all_leg_joints_rotate_about_pitch_axis(urdf_root) -> None:
    for joint_name in EXPECTED_JOINTS:
        assert joint_axis(urdf_root, joint_name) == PITCH_AXIS


@requires_xacro
def test_left_and_right_legs_are_mirrored(urdf_root) -> None:
    left_hip_y = joint_origin_y(urdf_root, "left_hip_joint")
    right_hip_y = joint_origin_y(urdf_root, "right_hip_joint")

    assert left_hip_y > 0.0
    assert right_hip_y < 0.0
    assert left_hip_y == pytest.approx(-right_hip_y)


@requires_xacro
def test_thigh_length_comes_from_config(urdf_root) -> None:
    config = yaml.safe_load(CONFIG_PATH.read_text(encoding="utf-8"))
    expected_thigh_length = config["geometry"]["thigh"]["length_m"]

    urdf_thigh_length = link_cylinder_length(urdf_root, "left_thigh")

    assert urdf_thigh_length == pytest.approx(expected_thigh_length)


@requires_xacro
@requires_check_urdf
def test_check_urdf_reports_valid_tree(tmp_path) -> None:
    urdf_path = tmp_path / "out.urdf"
    urdf_path.write_text(expand_xacro(XACRO_PATH), encoding="utf-8")

    completed = subprocess.run(["check_urdf", str(urdf_path)],
                               capture_output=True, text=True)

    assert completed.returncode == 0, completed.stderr
