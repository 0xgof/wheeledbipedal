"""Termination and truncation checks for the foundational environment.

This module separates unsafe-state termination from episode timeout truncation,
matching the Gymnasium API contract.
"""

from __future__ import annotations

from dataclasses import dataclass

from wheeled_biped_rl.simulation.robot_state import RobotState


@dataclass(frozen=True)
class TerminationDecision:
    """Gymnasium termination/truncation decision with a machine-readable reason."""

    terminated: bool
    truncated: bool
    reason: str | None


class TerminationChecker:
    """Classify unsafe robot states and episode timeouts.

    Falls produce ``terminated=True``. Reaching the configured step budget
    produces ``truncated=True`` without marking the state itself unsafe.
    """

    def __init__(self,
                 max_episode_steps: int,
                 max_abs_pitch_rad: float = 0.75,
                 min_body_height_m: float = 0.1) -> None:
        """Create a checker for fall and timeout conditions."""

        self.max_episode_steps = max_episode_steps
        self.max_abs_pitch_rad = max_abs_pitch_rad
        self.min_body_height_m = min_body_height_m

    def check(self,
              robot_state: RobotState,
              episode_step: int) -> TerminationDecision:
        """Return Gymnasium termination and truncation flags.

        Args:
            robot_state: Current reduced robot state.
            episode_step: One-based step count after the latest transition.
        """

        if abs(robot_state.body_pitch_rad) > self.max_abs_pitch_rad:
            decision = TerminationDecision(terminated=True,
                                           truncated=False,
                                           reason="fall_pitch")
            return decision

        if robot_state.body_z_m < self.min_body_height_m:
            decision = TerminationDecision(terminated=True,
                                           truncated=False,
                                           reason="fall_height")
            return decision

        if episode_step >= self.max_episode_steps:
            decision = TerminationDecision(terminated=False,
                                           truncated=True,
                                           reason="timeout")
            return decision

        decision = TerminationDecision(terminated=False,
                                       truncated=False,
                                       reason=None)
        return decision
