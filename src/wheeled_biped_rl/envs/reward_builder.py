"""Reward calculation for foundational environment smoke training.

The reward is intentionally simple in ``FL-2``. It provides named components so
early PPO experiments and observability logs can explain why a transition was
rewarded before the real dynamics/reward design matures.
"""

from __future__ import annotations

from dataclasses import dataclass

from wheeled_biped_rl.simulation.robot_state import RobotState


@dataclass(frozen=True)
class RewardBreakdown:
    """Total reward plus named component terms for diagnostics and logging."""

    total: float
    components: dict[str, float]


class RewardBuilder:
    """Calculate a simple balance-oriented placeholder reward.

    The current terms reward staying alive while penalizing torso pitch and
    large actuator commands. This is not the final task reward.
    """

    def __init__(self,
                 alive_reward: float = 1.0,
                 pitch_penalty_weight: float = 1.0,
                 action_penalty_weight: float = 0.01) -> None:
        """Create a reward builder with explicit component weights."""

        self.alive_reward = alive_reward
        self.pitch_penalty_weight = pitch_penalty_weight
        self.action_penalty_weight = action_penalty_weight

    def calculate(self, robot_state: RobotState) -> RewardBreakdown:
        """Calculate reward and component dictionary for one state.

        Args:
            robot_state: State whose previous action and pitch define the reward.

        Returns:
            Total scalar reward and component-level terms.
        """

        action = robot_state.previous_action
        action_magnitude = (abs(action.left_hip)
                            + abs(action.right_hip)
                            + abs(action.left_wheel)
                            + abs(action.right_wheel))
        pitch_penalty = -self.pitch_penalty_weight * abs(robot_state.body_pitch_rad)
        action_penalty = -self.action_penalty_weight * action_magnitude
        components = {
            "alive": self.alive_reward,
            "pitch_penalty": pitch_penalty,
            "action_penalty": action_penalty,
        }
        total_reward = sum(components.values())
        reward_breakdown = RewardBreakdown(total=float(total_reward),
                                           components=components)
        return reward_breakdown
