from pathlib import Path
import math

import pytest

from wheeled_biped_rl.envs.leg_kinematics import (
    RigidLegKinematics,
)
from wheeled_biped_rl.simulation.mechanism_config import (
    load_kollarcik_2021_rigid_config,
)


def make_kinematics() -> RigidLegKinematics:
    config = load_kollarcik_2021_rigid_config(Path("configs/robot/wheeled_biped.yaml"))
    kinematics = RigidLegKinematics(config)
    return kinematics


def test_forward_kinematics_returns_bounded_domain_named_leg_geometry() -> None:
    kinematics = make_kinematics()

    leg = kinematics.forward_side(hip_angle_rad=0.0,
                                  hip_velocity_rad_s=0.0,
                                  side="left")

    assert leg.side == "left"
    assert leg.hip_angle_rad == 0.0
    assert leg.leg_length_m == pytest.approx(0.433)
    assert leg.contact_point.x_m == pytest.approx(0.0)
    assert leg.contact_point.z_m == pytest.approx(-0.433)
    assert leg.constraint_residual_m == pytest.approx(0.0)
    assert leg.within_limits is True


def test_inverse_height_mapping_round_trips_through_forward_kinematics() -> None:
    kinematics = make_kinematics()
    target_height_m = 0.35

    hip_angle_rad = kinematics.inverse_height(target_height_m)
    leg = kinematics.forward_side(hip_angle_rad=hip_angle_rad,
                                  hip_velocity_rad_s=0.0,
                                  side="right")

    assert leg.side == "right"
    assert abs(leg.contact_point.z_m) == pytest.approx(target_height_m)
    assert kinematics.inverse_height(abs(leg.contact_point.z_m)) == pytest.approx(
        hip_angle_rad)


def test_constraint_residual_detects_invalid_leg_length() -> None:
    kinematics = make_kinematics()

    residual = kinematics.constraint_residual(hip_angle_rad=0.0,
                                              measured_leg_length_m=0.3)

    assert residual == pytest.approx(-0.133)


def test_velocity_residual_detects_inconsistent_vertical_velocity() -> None:
    kinematics = make_kinematics()

    residual = kinematics.velocity_residual(hip_angle_rad=math.radians(20.0),
                                            hip_velocity_rad_s=0.0,
                                            measured_vertical_velocity_m_s=0.2)

    assert residual == pytest.approx(0.2)


def test_inverse_height_rejects_unreachable_targets() -> None:
    kinematics = make_kinematics()

    with pytest.raises(ValueError, match="height target is outside reachable range"):
        kinematics.inverse_height(1.0)
