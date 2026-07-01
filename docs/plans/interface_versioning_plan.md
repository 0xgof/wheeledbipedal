# Plan - Interface Versioning

> Companion to `candidate_repository_implementation_plan.md`.
> This plan defines how action spaces, observation spaces, tasks, rewards, and backends
> receive stable ids before detailed implementation tickets are written.

---

## 1. Goal

Prevent silent incompatibility between checkpoints.

Every candidate must declare the policy-facing interface it was trained with:

```text
action_interface_id
observation_interface_id
task_id
reward_id
backend_id
robot_config_version
```

Without these ids, two checkpoints may look comparable while actually using different
inputs, outputs, reward scales, or simulator assumptions.

---

## 2. Interface IDs

Recommended initial ids:

```text
action_interface_id: hip_wheel_4d_v1
observation_interface_id: actor_obs_balance_v1
task_id: stand_balance_v1
reward_id: balance_v1
backend_id: python_sim_v1
```

Naming rules:

- use lowercase snake case;
- include a semantic version suffix such as `_v1`;
- bump the version when policy compatibility changes;
- do not reuse ids for changed meanings.

---

## 3. Action Interface Versioning

The action interface defines:

- action dimension;
- channel order;
- normalized range;
- scaling to physical command;
- clipping and rate limits;
- command mode: position, velocity, torque, or target abstraction;
- whether action smoothing or previous-action dependency is part of the interface.

Initial action interface:

```text
hip_wheel_4d_v1:
    shape: [4]
    order:
      - left_hip
      - right_hip
      - left_wheel
      - right_wheel
    normalized_range: [-1, 1]
    knee_action: false
```

Bump the version if any of these change.

---

## 4. Observation Interface Versioning

The observation interface defines:

- observation dimension;
- field order;
- units and normalization;
- history/frame-stack behavior;
- command vector fields;
- previous-action inclusion;
- deployable actor vs privileged critic split.

Initial observation interface should be deployable-only until privileged critic support is
actually implemented.

Example:

```text
actor_obs_balance_v1:
    fields:
      - body_pitch
      - body_pitch_rate
      - forward_velocity_estimate
      - left_hip_position
      - right_hip_position
      - left_hip_velocity
      - right_hip_velocity
      - left_wheel_velocity
      - right_wheel_velocity
      - previous_action[4]
      - command_forward_velocity
      - command_yaw_rate
```

Bump the version if field order, scaling, normalization, history, or available state
changes.

---

## 5. Task Interface Versioning

Task ids define:

- command distribution;
- reset distribution;
- success criteria;
- termination conditions;
- evaluation scenarios;
- curriculum stage when applicable.

Examples:

```text
stand_balance_v1
velocity_tracking_v1
yaw_tracking_v1
```

Do not hide task changes only inside reward weights. A changed reset or command
distribution may deserve a new task id.

---

## 6. Backend Interface Versioning

Backend ids define simulator assumptions:

- backend implementation;
- model fidelity;
- timestep;
- control period;
- integration method;
- contact model;
- actuator model;
- randomization profile support.

Examples:

```text
python_sim_v1
mujoco_linkage_bakeoff_v1
brax_mjx_linkage_bakeoff_v1
isaac_linkage_bakeoff_v1
gazebo_validation_v1
```

Backend ids are recorded in every candidate manifest and evaluation record.

---

## 7. Storage

Recommended config layout:

```text
configs/interfaces/
  action_hip_wheel_4d_v1.yaml
  observation_actor_balance_v1.yaml
  task_stand_balance_v1.yaml
  backend_python_sim_v1.yaml
```

The candidate repository snapshots these files into each candidate recipe so future
queries do not depend on mutable source files.

---

## 8. Tests

Interface tests should verify:

- declared action shape matches `ActionAdapter.action_space`;
- declared observation shape/order matches `ObservationBuilder.observation_space`;
- candidate manifests cannot omit interface ids;
- incompatible candidates are flagged by compare tooling;
- interface config snapshots are written into candidate recipes.

---

## NET

Action space, observation space, task, reward, and backend design should be versioned
before implementation tickets proliferate. The ids are what make model candidates
queryable and comparable.
