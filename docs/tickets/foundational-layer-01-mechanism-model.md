# FL-1 - Mechanism Model for Reduced-Order Linkage

- Status: `TODO`
- Stage: foundational layer / mechanism model
- Depends on: `CFG-2` preferred, but may start with direct YAML parsing if schema work is not ready
- Related: `FL-2`, `FL-3`
- Source plan: `docs/plans/foundational_layer_plan.md`
- Goal: define the robot state/action data model and the first reduced-order constrained-leg kinematics.

## Problem

The RL layer must not treat the robot as a serial hip/knee tree with an actuated knee.
The physical robot has per-side hip and wheel actuation, while the knee/linkage state is
derived or passive. Layer 1 needs a simple, explicit mechanism model before any
Gymnasium environment or dynamics loop can be trusted.

## Scope

1. Create the importable Python package skeleton if it does not exist.
2. Define `RobotState` and `RobotAction` dataclasses.
3. Define a 4-D action convention:
   - left hip command
   - right hip command
   - left wheel command
   - right wheel command
4. Implement `leg_kinematics.py` for the rigid no-spring v1 linkage approximation.
5. Provide forward mapping from hip/motor coordinate to derived leg state:
   - effective leg length or body-height contribution;
   - derived knee/linkage angle placeholder;
   - wheel/contact pose relative to body.
6. Provide inverse mapping from leg target/posture target back to hip command where
   meaningful for v1.
7. Load dimensions and limits from the canonical robot YAML or typed `RobotConfig`.
8. Keep spring and lift-off/contact dynamics out of v1, but leave fields compatible with
   later optional additions.

## Non-goals

- Gymnasium environment implementation.
- PPO/Tianshou training.
- MuJoCo, Brax/MJX, Isaac, Gazebo, or ROS 2 integration.
- full closed-chain DAE dynamics.
- actuated knee control.

## Files

- `src/wheeled_biped_rl/simulation/robot_state.py`
- `src/wheeled_biped_rl/envs/leg_kinematics.py`
- `src/wheeled_biped_rl/utils/config.py` or config-schema files only if needed
- `tests/test_leg_kinematics.py`
- `tests/test_robot_state.py`

## Acceptance

- `RobotAction` exposes exactly the 4 intended actuator channels and no knee action.
- `RobotState` contains body pitch/pitch rate, forward position/velocity, per-side hip
  state, wheel state, previous action, and contact flags.
- Forward kinematics returns deterministic, bounded leg geometry over the configured hip
  range.
- Inverse mapping is consistent with forward mapping over representative safe hip/height
  samples.
- Invalid geometry, out-of-range hip values, or impossible inverse targets fail clearly.

## Validation

- TDD required.
- Initial test run must fail before implementation for the missing mechanism behavior.
- Final validation:
  - `pytest tests/test_robot_state.py tests/test_leg_kinematics.py`
- Final summary must include:
  - tests added or changed;
  - initial failing result;
  - final passing result;
  - any assumptions in the reduced-order linkage approximation.
