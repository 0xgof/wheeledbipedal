"""Rigid reduced leg kinematics for the foundational model.

The first implementation uses a deliberately simple rigid no-spring approximation:
the hip angle determines an effective leg vector of fixed length. The API exposes
domain-named geometry and residual diagnostics while keeping the reduced coordinate
contract available for later dynamics work.
"""

from __future__ import annotations

from dataclasses import dataclass
import math

from wheeled_biped_rl.simulation.mechanism_config import RobotMechanismConfig


@dataclass(frozen=True)
class Point2D:
    """Planar point in the body side-view frame."""

    x_m: float
    z_m: float


@dataclass(frozen=True)
class LegGeometry:
    """Domain-named derived geometry for one reduced rigid leg."""

    side: str
    hip_angle_rad: float
    hip_velocity_rad_s: float
    leg_length_m: float
    knee_angle_rad: float
    contact_point: Point2D
    constraint_residual_m: float
    velocity_residual_m_s: float
    within_limits: bool


@dataclass(frozen=True)
class MechanismDiagnostics:
    """Residual and limit diagnostics for reduced mechanism states."""

    max_position_residual_m: float
    max_velocity_residual_m_s: float
    within_limits: bool
    jacobian_condition_number: float | None = None


class RigidLegKinematics:
    """Forward, inverse, and residual checks for the v1 rigid linkage."""

    def __init__(self, mechanism_config: RobotMechanismConfig) -> None:
        """Create kinematics from a resolved mechanism config."""

        self.mechanism_config = mechanism_config
        self.leg_length_m = mechanism_config.geometry.rigid_leg_length_m

    def forward_side(self,
                     hip_angle_rad: float,
                     hip_velocity_rad_s: float,
                     side: str) -> LegGeometry:
        """Map one hip coordinate to deterministic derived leg geometry."""

        self._require_side(side)
        contact_x_m = self.leg_length_m * math.sin(hip_angle_rad)
        contact_z_m = -self.leg_length_m * math.cos(hip_angle_rad)
        vertical_velocity_m_s = self.vertical_velocity(hip_angle_rad,
                                                       hip_velocity_rad_s)
        within_limits = self._within_hip_limits(hip_angle_rad)
        leg_geometry = LegGeometry(
            side=side,
            hip_angle_rad=hip_angle_rad,
            hip_velocity_rad_s=hip_velocity_rad_s,
            leg_length_m=self.leg_length_m,
            knee_angle_rad=-abs(hip_angle_rad),
            contact_point=Point2D(x_m=contact_x_m, z_m=contact_z_m),
            constraint_residual_m=0.0,
            velocity_residual_m_s=0.0 if within_limits else vertical_velocity_m_s,
            within_limits=within_limits)
        return leg_geometry

    def inverse_height(self, target_height_m: float) -> float:
        """Map a reachable absolute leg height to a hip angle."""

        if target_height_m <= 0.0 or target_height_m > self.leg_length_m:
            raise ValueError("height target is outside reachable range")
        height_ratio = target_height_m / self.leg_length_m
        hip_angle_rad = math.acos(height_ratio)
        return hip_angle_rad

    def constraint_residual(self,
                            hip_angle_rad: float,
                            measured_leg_length_m: float) -> float:
        """Return loop-length residual for a measured derived leg length."""

        expected_leg_length_m = self.leg_length_m
        residual_m = measured_leg_length_m - expected_leg_length_m
        return residual_m

    def vertical_velocity(self,
                          hip_angle_rad: float,
                          hip_velocity_rad_s: float) -> float:
        """Return contact vertical velocity implied by hip motion."""

        vertical_velocity_m_s = (self.leg_length_m
                                 * math.sin(hip_angle_rad)
                                 * hip_velocity_rad_s)
        return vertical_velocity_m_s

    def velocity_residual(self,
                          hip_angle_rad: float,
                          hip_velocity_rad_s: float,
                          measured_vertical_velocity_m_s: float) -> float:
        """Return residual between measured and Jacobian-implied vertical velocity."""

        expected_vertical_velocity_m_s = self.vertical_velocity(
            hip_angle_rad=hip_angle_rad,
            hip_velocity_rad_s=hip_velocity_rad_s)
        residual_m_s = measured_vertical_velocity_m_s - expected_vertical_velocity_m_s
        return residual_m_s

    def diagnostics(self,
                    left_leg: LegGeometry,
                    right_leg: LegGeometry) -> MechanismDiagnostics:
        """Summarize residuals and limits across both reduced legs."""

        max_position_residual_m = max(abs(left_leg.constraint_residual_m),
                                      abs(right_leg.constraint_residual_m))
        max_velocity_residual_m_s = max(abs(left_leg.velocity_residual_m_s),
                                        abs(right_leg.velocity_residual_m_s))
        within_limits = left_leg.within_limits and right_leg.within_limits
        diagnostics = MechanismDiagnostics(
            max_position_residual_m=max_position_residual_m,
            max_velocity_residual_m_s=max_velocity_residual_m_s,
            within_limits=within_limits,
            jacobian_condition_number=1.0)
        return diagnostics

    def _within_hip_limits(self, hip_angle_rad: float) -> bool:
        """Return whether the hip angle is within configured safety limits."""

        lower_limit = self.mechanism_config.hip_limit_lower_rad
        upper_limit = self.mechanism_config.hip_limit_upper_rad
        within_limits = lower_limit <= hip_angle_rad <= upper_limit
        return within_limits

    def _require_side(self, side: str) -> None:
        """Require a supported leg side name."""

        if side not in ("left", "right"):
            raise ValueError("side must be 'left' or 'right'")
