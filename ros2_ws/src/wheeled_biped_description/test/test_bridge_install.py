"""Config-bridge tests for the ROS 2 display vertical (RVT-1).

Requires the package to be built/installed (ament index resolvable); the whole module
skips otherwise. Specifies that the config installed into the package share is an exact,
build-time copy of the canonical source. Fails until BRG-1 installs the config.
"""
from pathlib import Path

import pytest

pytest.importorskip("ament_index_python.packages")

REPO_ROOT = Path(__file__).resolve().parents[4]
CANONICAL_CONFIG = REPO_ROOT / "configs" / "robot" / "wheeled_biped.yaml"


def installed_config_path() -> Path:
    from ament_index_python.packages import get_package_share_directory
    share_dir = Path(get_package_share_directory("wheeled_biped_description"))
    config_path = share_dir / "config" / "wheeled_biped.yaml"
    return config_path


def test_installed_config_exists() -> None:
    installed = installed_config_path()

    assert installed.is_file(), f"config not installed into share: {installed}"


def test_installed_config_matches_canonical() -> None:
    installed = installed_config_path()

    installed_text = installed.read_text(encoding="utf-8")
    canonical_text = CANONICAL_CONFIG.read_text(encoding="utf-8")

    assert installed_text == canonical_text
