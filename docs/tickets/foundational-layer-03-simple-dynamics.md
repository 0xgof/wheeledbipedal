# FL-3 - Simple Reduced Dynamics for Foundational Training

- Status: `TODO`
- Stage: foundational layer / simple dynamics
- Depends on: `FL-1`, `FL-2`
- Related: robusting backend feasibility tickets later
- Source plan: `docs/plans/foundational_layer_plan.md`
- Goal: replace placeholder stepping with deterministic reduced-order dynamics suitable for first PPO balance experiments.

## Problem

The foundational environment needs enough dynamics to test whether the RL formulation is
coherent. The model should be simple and fast, but it must preserve the important control
structure: body pitch balance, wheel-driven forward motion, hip/posture influence, action
limits, and no independently actuated knee.

## Scope

1. Implement reduced-order state integration in `simple_dynamics.py`.
2. Track at least:
   - body pitch and pitch rate;
   - forward position and velocity;
   - left/right hip positions and velocities;
   - left/right wheel velocities;
   - effective body height or leg-length state;
   - previous action.
3. Include simple effects:
   - gravity-driven pitch instability;
   - wheel command influence on forward acceleration and pitch recovery;
   - hip command influence on body height/posture;
   - actuator velocity/torque clipping from config;
   - basic damping.
4. Implement a deterministic integrator, likely semi-implicit Euler.
5. Add reset initial-state sampling with seed control.
6. Wire `PythonSimBackend.step` to use the dynamics.
7. Keep noise, delay, slip randomization, spring, and hybrid contact out of this ticket
   unless needed for a tiny deterministic placeholder.

## Non-goals

- physical fidelity sufficient for final training.
- full linkage DAE or contact-rich dynamics.
- domain randomization.
- MuJoCo/Brax/Isaac/Gazebo implementation.
- proving PPO learns; this ticket only makes the environment trainable.

## Files

- `src/wheeled_biped_rl/simulation/simple_dynamics.py`
- `src/wheeled_biped_rl/simulation/integration.py`
- `src/wheeled_biped_rl/backends/python_sim_backend.py`
- `src/wheeled_biped_rl/envs/reward_builder.py` only if reward terms need minor tuning
- `src/wheeled_biped_rl/envs/termination.py` only if dynamics exposes new unsafe states
- `tests/test_simple_dynamics.py`
- `tests/test_python_sim_backend.py`
- existing env tests from `FL-2`

## Acceptance

- Zero action from an upright nominal state remains finite and deterministic for a short
  rollout.
- An unsafe pitch state terminates through the environment.
- Wheel commands influence forward velocity in the expected direction.
- Corrective wheel commands can reduce pitch rate or pitch error in a controlled
  unit-level scenario.
- Hip commands change effective height/posture within configured limits.
- Integration is deterministic for a fixed seed and action sequence.
- State values remain finite under clipped random actions for a representative rollout.

## Validation

- TDD required.
- Initial test run must fail before implementation for missing or incorrect dynamics.
- Final validation:
  - `pytest tests/test_simple_dynamics.py tests/test_python_sim_backend.py tests/test_env_api.py`
- Broader validation:
  - `python -m compileall -q src tests`
- Optional smoke:
  - run a short random-policy rollout script or env loop for 1000 steps and report no NaN/Inf.
- Final summary must include:
  - tests added or changed;
  - initial failing result;
  - final passing result;
  - known simplifications of the dynamics model.
