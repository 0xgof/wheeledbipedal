"""Backend-neutral render state for rollout visualization."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


@dataclass(frozen=True)
class BodyRenderState:
    """Renderable body pose and dimensions in a simple world frame."""

    x_m: float
    z_m: float
    pitch_rad: float
    size_x_m: float
    size_y_m: float
    size_z_m: float


@dataclass(frozen=True)
class WheelRenderState:
    """Renderable wheel pose and spin state."""

    side: str
    x_m: float
    z_m: float
    radius_m: float
    width_m: float
    angle_rad: float
    angular_velocity_rad_s: float
    contact: bool


@dataclass(frozen=True)
class LegRenderState:
    """Renderable reduced leg geometry for one side."""

    side: str
    hip_angle_rad: float
    knee_angle_rad: float
    leg_length_m: float
    hip_x_m: float
    hip_z_m: float
    contact_x_m: float
    contact_z_m: float
    contact: bool


@dataclass(frozen=True)
class DiagnosticsRenderState:
    """Renderable mechanism diagnostics for a rollout frame."""

    max_position_residual_m: float
    max_velocity_residual_m_s: float
    within_limits: bool
    jacobian_condition_number: float | None


@dataclass(frozen=True)
class RenderState:
    """Backend-neutral visualization state for one rollout frame."""

    step: int
    time_s: float
    body: BodyRenderState
    left_wheel: WheelRenderState
    right_wheel: WheelRenderState
    left_leg: LegRenderState
    right_leg: LegRenderState
    diagnostics: DiagnosticsRenderState

    def to_dict(self) -> dict[str, Any]:
        """Serialize the render state to plain JSON-compatible data."""

        render_state_dict = asdict(self)
        return render_state_dict

    @classmethod
    def from_dict(cls, render_state_dict: dict[str, Any]) -> "RenderState":
        """Reconstruct a render state from plain serialized fields."""

        render_state = cls(
            step=int(render_state_dict["step"]),
            time_s=float(render_state_dict["time_s"]),
            body=BodyRenderState(**render_state_dict["body"]),
            left_wheel=WheelRenderState(**render_state_dict["left_wheel"]),
            right_wheel=WheelRenderState(**render_state_dict["right_wheel"]),
            left_leg=LegRenderState(**render_state_dict["left_leg"]),
            right_leg=LegRenderState(**render_state_dict["right_leg"]),
            diagnostics=DiagnosticsRenderState(**render_state_dict["diagnostics"]))
        return render_state
