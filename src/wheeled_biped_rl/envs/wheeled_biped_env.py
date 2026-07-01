"""Gymnasium API surface for the foundational wheeled-biped environment.

``WheeledBipedEnv`` is the policy-facing Layer 1 entry point. It coordinates
action adaptation, backend stepping, observation construction, rewards,
termination checks, and optional observability without importing ROS 2.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np
from gymnasium import Env

from wheeled_biped_rl.backends.base_backend import BaseBackend
from wheeled_biped_rl.backends.python_sim_backend import PythonSimBackend
from wheeled_biped_rl.envs.action_adapter import ActionAdapter
from wheeled_biped_rl.envs.leg_kinematics import RigidLegKinematics
from wheeled_biped_rl.envs.observation_builder import ObservationBuilder
from wheeled_biped_rl.envs.reward_builder import RewardBuilder
from wheeled_biped_rl.envs.termination import TerminationChecker
from wheeled_biped_rl.observability.logger import JsonlExperimentLogger
from wheeled_biped_rl.simulation.mechanism_config import (
    RobotMechanismConfig,
    load_kollarcik_2021_rigid_config,
)
from wheeled_biped_rl.simulation.robot_state import RobotAction, RobotState
from wheeled_biped_rl.visualization.adapters import render_state_from_robot_state
from wheeled_biped_rl.visualization.plugins.gym_render_sink import RgbArrayRenderer
from wheeled_biped_rl.visualization.render_state import RenderState


class WheeledBipedEnv(Env):
    """Gymnasium-compatible environment for Layer 1 RL formulation work.

    The class intentionally owns orchestration only. Physics fidelity is supplied
    by the backend, starting with a deterministic placeholder and later replaced
    by the reduced ODE solver.
    """

    metadata = {"render_modes": [None, "rgb_array"]}

    def __init__(self,
                 mechanism_config: RobotMechanismConfig | None = None,
                 backend: BaseBackend | None = None,
                 max_episode_steps: int = 500,
                 dt_s: float = 0.02,
                 render_mode: str | None = None,
                 observability_logger: JsonlExperimentLogger | None = None) -> None:
        """Create the environment shell around a reduced simulation backend."""

        if render_mode not in (None, "rgb_array"):
            raise ValueError("render_mode must be None or 'rgb_array'")
        self.mechanism_config = mechanism_config or load_kollarcik_2021_rigid_config(
            Path("configs/robot/wheeled_biped.yaml"))
        self.backend = backend or PythonSimBackend(self.mechanism_config)
        self.action_adapter = ActionAdapter(self.mechanism_config)
        self.observation_builder = ObservationBuilder(self.mechanism_config)
        self.reward_builder = RewardBuilder()
        self.kinematics = RigidLegKinematics(self.mechanism_config)
        self.rgb_renderer = RgbArrayRenderer()
        self.termination_checker = TerminationChecker(
            max_episode_steps=max_episode_steps)
        self.action_space = self.action_adapter.space
        self.observation_space = self.observation_builder.space
        self.max_episode_steps = max_episode_steps
        self.dt_s = dt_s
        self.render_mode = render_mode
        self.observability_logger = observability_logger
        self.episode_step = 0
        self.episode_index = 0
        self.state: RobotState | None = None

    def reset(self,
              seed: int | None = None,
              options: dict[str, Any] | None = None) -> tuple[np.ndarray, dict[str, Any]]:
        """Reset the backend and return the initial observation and info.

        The same seed must produce the same placeholder initial state. ``options``
        is accepted for Gymnasium compatibility and reserved for later reset
        distributions.
        """

        super().reset(seed=seed)
        self.episode_step = 0
        self.episode_index += 1
        self.state = self.backend.reset(seed=seed)
        observation = self.observation_builder.build(self.state)
        reset_reason = "seeded_reset" if seed is not None else "reset"
        info = {
            "episode_step": self.episode_step,
            "episode_index": self.episode_index,
            "reset_reason": reset_reason,
        }
        self._log_info(event_type="env_reset",
                       message="Environment reset",
                       payload={"reset_reason": reset_reason})
        return observation, info

    def step(self,
             action: np.ndarray) -> tuple[np.ndarray, float, bool, bool, dict[str, Any]]:
        """Apply one action and return the Gymnasium step tuple.

        The raw policy action is clipped/scaled by ``ActionAdapter`` before the
        backend sees it. Returned ``info`` includes reward components, previous
        action, backend diagnostics, and termination reason.
        """

        adapted_action = self.action_adapter.adapt(action)
        backend_step = self.backend.step(action=adapted_action, dt_s=self.dt_s)
        self.state = backend_step.state
        self.episode_step += 1

        observation = self.observation_builder.build(self.state)
        reward_breakdown = self.reward_builder.calculate(self.state)
        decision = self.termination_checker.check(self.state, self.episode_step)
        info = self._step_info(adapted_action=adapted_action,
                               reward_components=reward_breakdown.components,
                               termination_reason=decision.reason,
                               backend_diagnostics=backend_step.diagnostics)

        if decision.terminated or decision.truncated:
            self._log_info(event_type="env_episode_finished",
                           message="Environment episode finished",
                           step=self.episode_step,
                           payload={"termination_reason": decision.reason})

        step_tuple = (observation,
                      reward_breakdown.total,
                      decision.terminated,
                      decision.truncated,
                      info)
        return step_tuple

    def close(self) -> None:
        """Close the backend and release any backend-owned resources."""

        self.backend.close()

    def render(self) -> np.ndarray | None:
        """Return an RGB array when configured for ``render_mode='rgb_array'``."""

        if self.render_mode is None:
            return None
        current_render_state = self.render_state()
        rgb_array = self.rgb_renderer.render(current_render_state)
        return rgb_array

    def render_state(self) -> RenderState:
        """Return the backend-neutral render state for the current env state."""

        if self.state is None:
            raise RuntimeError("reset must be called before render_state")
        current_render_state = render_state_from_robot_state(
            robot_state=self.state,
            mechanism_config=self.mechanism_config,
            kinematics=self.kinematics,
            step=self.episode_step,
            time_s=self.episode_step * self.dt_s)
        return current_render_state

    def _step_info(self,
                   adapted_action: RobotAction,
                   reward_components: dict[str, float],
                   termination_reason: str | None,
                   backend_diagnostics: dict[str, float | bool | str]) -> dict[str, Any]:
        """Build the diagnostic info dictionary for one step."""

        info = {
            "episode_step": self.episode_step,
            "episode_index": self.episode_index,
            "previous_action": _action_to_info(adapted_action),
            "reward_components": dict(reward_components),
            "termination_reason": termination_reason,
            "backend_diagnostics": dict(backend_diagnostics),
        }
        return info

    def _log_info(self,
                  event_type: str,
                  message: str,
                  step: int | None = None,
                  payload: dict[str, Any] | None = None) -> None:
        """Write an optional observability event for environment orchestration."""

        if self.observability_logger is None:
            return None
        self.observability_logger.info(event_type=event_type,
                                       message=message,
                                       step=step,
                                       episode=self.episode_index,
                                       payload=payload)
        return None


def _action_to_info(action: RobotAction) -> dict[str, float]:
    """Serialize an action for stable, compact ``info`` dictionaries."""

    action_info = {
        "left_hip": round(action.left_hip, 3),
        "right_hip": round(action.right_hip, 3),
        "left_wheel": round(action.left_wheel, 3),
        "right_wheel": round(action.right_wheel, 3),
    }
    return action_info
