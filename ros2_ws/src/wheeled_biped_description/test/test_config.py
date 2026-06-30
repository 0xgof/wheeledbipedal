"""Config-layer tests for the ROS 2 display vertical (RVT-1).

Pure-Python (PyYAML only) — runnable without ROS. Specifies the canonical robot config
that both the RL env and the ROS Xacro consume. Tests-first: they fail until CFG-1
promotes `configs/robot/wheeled_biped.yaml`.
"""
from pathlib import Path

import pytest
import yaml

REPO_ROOT = Path(__file__).resolve().parents[4]
CONFIG_PATH = REPO_ROOT / "configs" / "robot" / "wheeled_biped.yaml"


@pytest.fixture
def robot_config() -> dict:
    assert CONFIG_PATH.is_file(), f"canonical config missing: {CONFIG_PATH}"
    parsed = yaml.safe_load(CONFIG_PATH.read_text(encoding="utf-8"))
    return parsed


def test_config_file_exists() -> None:
    assert CONFIG_PATH.is_file(), f"canonical config missing: {CONFIG_PATH}"


def test_config_parses_as_mapping(robot_config) -> None:
    assert isinstance(robot_config, dict)


def test_required_sections_present(robot_config) -> None:
    required = {"meta", "geometry", "joints"}

    missing = required - set(robot_config)

    assert not missing, f"missing config sections: {sorted(missing)}"


def test_link_dimensions_are_positive(robot_config) -> None:
    geometry = robot_config["geometry"]

    assert geometry["thigh"]["length_m"] > 0.0
    assert geometry["shank"]["length_m"] > 0.0
    assert geometry["wheel"]["radius_m"] > 0.0


def test_spring_disabled_by_default(robot_config) -> None:
    spring = robot_config.get("spring", {})

    assert spring.get("enabled") is False


def test_config_declares_version(robot_config) -> None:
    assert "config_version" in robot_config["meta"]
