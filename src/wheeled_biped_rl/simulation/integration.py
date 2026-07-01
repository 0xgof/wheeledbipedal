"""Small deterministic integration helpers for reduced dynamics."""

from __future__ import annotations


def semi_implicit_euler(position: float,
                        velocity: float,
                        acceleration: float,
                        dt_s: float) -> tuple[float, float]:
    """Integrate one scalar coordinate with semi-implicit Euler."""

    next_velocity = velocity + acceleration * dt_s
    next_position = position + next_velocity * dt_s
    integrated_state = (next_position, next_velocity)
    return integrated_state


def clamp(value: float,
          lower: float,
          upper: float) -> float:
    """Clamp a scalar value to inclusive lower and upper bounds."""

    clamped_value = max(lower, min(upper, value))
    return clamped_value
