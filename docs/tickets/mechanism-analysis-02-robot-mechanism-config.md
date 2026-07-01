# MECH-2 - RobotMechanismConfig for First ODE/DOF Consumer

- Status: `Done`
- Stage: foundational layer / mechanism configuration
- Depends on: `MECH-1`
- Related: `FL-1`, `FL-3`, `VIS-1`
- Source plan: `docs/plans/robot_mechanism_versioning_plan.md`
- Goal: define the typed configuration that turns thesis-derived robot data and a model choice into the first concrete consumer of the ODE/DOF solver.

## Problem

The ODE/DOF solver should not consume raw thesis numbers directly. The current
physical source of truth is `configs/robot/wheeled_biped.yaml`, grounded in
`docs/robot/robot_description.md` and the Kollarčík 2021 thesis. The solver needs a
resolved mechanism configuration that states how those physical values are interpreted
as reduced coordinates, actuator inputs, constraints, diagnostics, and observability.

Without this bridge, `FL-1` would mix physical parameters, model assumptions, and solver
state layout in implementation code.

## Scope

1. Define `RobotMechanismConfig` or equivalent typed schema.
2. Define the first concrete mechanism id:
   - `kollarcik_2021_rigid_v1`.
3. Resolve the config from:
   - `configs/robot/wheeled_biped.yaml`;
   - `docs/robot/robot_description.md` / Kollarčík 2021 reference assumptions;
   - v1 model choices from `MECH-1`.
4. Include mechanism metadata:
   - source reference;
   - config id;
   - model level;
   - spring enabled/disabled;
   - contact model level;
   - reduced model version.
5. Define reduced coordinate names and order:
   - `q`;
   - `qdot`;
   - actuator input `u`.
6. Define actuator command order and modes:
   - left hip;
   - right hip;
   - left wheel;
   - right wheel.
7. Define required geometry and inertial parameters for the v1 solver.
8. Define constraint and diagnostic names:
   - `c(q)`;
   - `J(q)`;
   - `J(q) @ qdot`;
   - position residual norm;
   - velocity residual norm;
   - limit violation;
   - optional Jacobian condition number.
9. Define deployable versus privileged fields for observation builders.
10. Keep the schema explicit enough for candidate/version tracking.

## First Config Boundary

`kollarcik_2021_rigid_v1` means:

- thesis-derived reference parameters;
- reduced-order mechanism model;
- rigid no-spring leg;
- no full closed-chain DAE;
- no hybrid lift-off/contact dynamics;
- no simulator backend dependency;
- no knee action;
- 4-D action convention: left hip, right hip, left wheel, right wheel.

This config is a mechanism-model interpretation of the physical YAML. It is not a
replacement for the physical robot YAML.

## Expected Shape

The implementation does not need to use this exact YAML syntax, but the resolved data
must cover these concepts:

```yaml
mechanism:
  id: kollarcik_2021_rigid_v1
  topology: ascento_class_closed_chain
  model_level: reduced_order
  spring_enabled: false

coordinates:
  reduced_q:
    - body_pitch_rad
    - body_x_m
    - body_z_m
    - left_hip_rad
    - right_hip_rad
    - left_wheel_rad
    - right_wheel_rad
  reduced_qdot:
    - body_pitch_rad_s
    - body_x_m_s
    - body_z_m_s
    - left_hip_rad_s
    - right_hip_rad_s
    - left_wheel_rad_s
    - right_wheel_rad_s

actuators:
  action_order:
    - left_hip
    - right_hip
    - left_wheel
    - right_wheel
  hip_mode: position_target_or_torque
  wheel_mode: torque

constraints:
  type: closed_chain_reduced
  position_residual: c_q
  velocity_residual: j_q_qdot

observability:
  actor_measured:
    - motor_positions
    - motor_velocities
    - motor_torques
    - imu_pitch
    - imu_roll
    - imu_rates
  privileged:
    - full_linkage_state
    - exact_body_velocity
    - contact_forces
    - constraint_residuals
```

## Non-goals

- Implementing the ODE solver.
- Implementing kinematics.
- Implementing Gymnasium environment APIs.
- Adding MuJoCo, Brax/MJX, Isaac, Gazebo, or ROS 2 dependencies.
- Replacing `configs/robot/wheeled_biped.yaml`.
- Calibrating thesis placeholders to real hardware.

## Files

- `docs/analysis/mechanism_dof.md` if the config definition belongs in the analysis deliverable
- `configs/robot/wheeled_biped.yaml` only if missing required physical fields
- future implementation files likely under `src/wheeled_biped_rl/simulation/` or `src/wheeled_biped_rl/utils/config.py`
- future tests likely `tests/test_robot_mechanism_config.py`

## Acceptance

- The ticket or analysis deliverable defines the resolved `RobotMechanismConfig`
  concept clearly enough for `FL-1` tests.
- The physical YAML remains the source of physical parameters.
- The mechanism config captures the v1 model interpretation separately from raw
  physical parameters.
- Coordinate, velocity, and action ordering are explicit and stable.
- Reduced-model simplifications are named and versionable.
- Observation fields distinguish deployable actor inputs from privileged/debug state.
- The config can be referenced by the controller candidate registry as a robot/mechanism
  assumption.

## Validation

- Documentation/schema-design ticket; TDD is not required unless implementation code is
  added.
- Validate by checking that `FL-1` can consume the config definition without inventing
  coordinate ordering, action ordering, or v1 simplification assumptions.
