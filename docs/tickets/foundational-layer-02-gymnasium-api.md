# FL-2 - Gymnasium API for WheeledBipedEnv

- Status: `TODO`
- Stage: foundational layer / environment API
- Depends on: `FL-1`
- Related: `FL-3`
- Source plan: `docs/plans/foundational_layer_plan.md`
- Goal: expose the reduced robot model through a Gymnasium-compatible environment that Tianshou can consume.

## Problem

Tianshou should interact only with a standard environment API. The repository needs a
`WheeledBipedEnv` that owns observation construction, action adaptation, reward
calculation, termination, reset logic, episode bookkeeping, and backend orchestration
without importing ROS 2 or any high-fidelity simulator.

## Scope

1. Implement `WheeledBipedEnv` with the Gymnasium API:
   - `reset(seed=None, options=None) -> (observation, info)`
   - `step(action) -> (observation, reward, terminated, truncated, info)`
2. Implement `BaseBackend` protocol with `reset`, `step`, and `close`.
3. Implement a minimal `PythonSimBackend` placeholder that can reset and step a
   deterministic state; `FL-3` will replace placeholder dynamics with actual simple
   dynamics if needed.
4. Implement `ActionAdapter` for normalized `Box(-1, 1, shape=(4,))` actions.
5. Implement `ObservationBuilder` for deployable actor observations.
6. Implement `RewardBuilder` with component dictionary support, even if early terms are
   simple.
7. Implement `TerminationChecker` for fall and timeout conditions.
8. Include episode step count, previous action, command vector, reward components, and
   reset reason in `info` where appropriate.

## Non-goals

- learning success or PPO convergence.
- high-fidelity physics.
- Gazebo/ROS 2 integration.
- privileged critic observations unless they are trivial to include without expanding scope.

## Files

- `src/wheeled_biped_rl/envs/wheeled_biped_env.py`
- `src/wheeled_biped_rl/envs/action_adapter.py`
- `src/wheeled_biped_rl/envs/observation_builder.py`
- `src/wheeled_biped_rl/envs/reward_builder.py`
- `src/wheeled_biped_rl/envs/termination.py`
- `src/wheeled_biped_rl/backends/base_backend.py`
- `src/wheeled_biped_rl/backends/python_sim_backend.py`
- `tests/test_env_api.py`
- `tests/test_action_adapter.py`
- `tests/test_observation_builder.py`
- `tests/test_reward_builder.py`
- `tests/test_termination.py`

## Acceptance

- `WheeledBipedEnv` passes Gymnasium reset/step contract tests.
- Observation and action spaces are deterministic and match actual returned values.
- Actions are clipped/scaled through `ActionAdapter`; raw policy output never directly
  mutates state.
- Reset with the same seed is reproducible.
- `terminated` is used for falls/unsafe state; `truncated` is used for episode timeout.
- `info["reward_components"]` exposes component-level reward values.
- No environment module imports ROS 2.

## Validation

- TDD required.
- Initial test run must fail before implementation for the missing env API behavior.
- Final validation:
  - `pytest tests/test_env_api.py tests/test_action_adapter.py tests/test_observation_builder.py tests/test_reward_builder.py tests/test_termination.py`
- Broader validation:
  - `python -m compileall -q src tests`
- Final summary must include initial failing and final passing results.
