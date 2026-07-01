# Plan - Gazebo Validation and Feedback Layer

> Companion to `robusting_layer_plan.md`.
> This plan defines the third layer: Gazebo + ROS 2 validation, plus an optional
> checkpoint feedback path back into the robusting training layer.

---

## 1. Goal

Use Gazebo + ROS 2 to validate trained policies inside the robotics integration stack.

This layer should answer:

```text
Does the policy survive ROS 2 message flow, sensors, controllers, timing, latency,
robot description compatibility, and deployment assumptions?
```

It should not be the default PPO/SAC environment-step factory.

---

## 2. Scope

Implement:

- Gazebo/SDF or Gazebo-compatible robot model.
- ROS 2 launch for simulator validation.
- policy evaluation node or bridge that loads a trained checkpoint/export.
- deterministic scenario runner.
- metrics extraction from ROS topics, simulator state, and policy output.
- optional feedback result consumed by the robusting layer.

Do not implement:

- online RL collection through Gazebo as the default training loop;
- GUI-dependent acceptance as the only validation;
- hardware control without the safety layer.

---

## 3. Validation Scenarios

Start with deterministic scenarios:

- upright balance from nominal initial state;
- small initial pitch offset;
- commanded zero velocity;
- forward velocity command;
- yaw command if the simulator model supports lateral dynamics;
- sensor delay profile;
- actuator saturation profile;
- friction/slip profile;
- controller timing jitter profile.

Each scenario should specify:

```text
initial state
command sequence
random seed
duration
pass/fail thresholds
metrics to record
```

---

## 4. Metrics

Minimum metrics:

- fall / no fall;
- survival time;
- pitch and roll RMS;
- velocity tracking error;
- wheel slip or contact anomaly count when available;
- max motor command;
- action smoothness;
- controller deadline misses;
- ROS topic delay and dropped-message counts;
- safety-supervisor interventions.

Validation should produce a machine-readable result:

```text
checkpoint_id
scenario_id
pass/fail
score
metric summary
failure reason
artifact paths
```

---

## 5. Feedback to Robusting Layer

Gazebo can feed the robusting layer in two modes.

### 5.1 Checkpoint Gate

Use Gazebo as a deterministic acceptance gate.

Flow:

```text
robusting trainer saves checkpoint
local deterministic eval runs first
Gazebo validation runs only for candidates
result is written to a validation artifact
trainer promotes, continues, pauses, or rejects according to config
```

This is the first mode to implement because it is simple and low-risk.

### 5.2 Curriculum Feedback

Use Gazebo failures to adjust later robusting runs.

Examples:

- increase friction randomization after slip failures;
- increase action-delay randomization after timing failures;
- add reset states around the failing pose;
- adjust evaluation weights used for checkpoint ranking.

This mode should be added only after checkpoint gating works. Keep it explicit and
config-driven; do not make Gazebo silently mutate training settings.

---

## 6. Determinism

Gazebo validation must be as deterministic as practical:

- fixed scenario seeds;
- fixed initial states;
- pinned simulator and ROS versions;
- logged config snapshot;
- no GUI requirement;
- consistent controller update periods;
- machine-readable artifacts;
- replayable launch commands.

Some simulator nondeterminism is expected. Treat results statistically only when
necessary, and record repeated runs explicitly.

---

## 7. HPC / Remote Execution

Gazebo validation may run in a ROS-enabled environment separate from the robusting
trainer.

Support:

- local headless validation;
- remote validation job submission;
- artifact handoff by checkpoint path or exported policy path;
- timeout and failure handling;
- validation result polling;
- validation result ingestion by the robusting trainer.

The robusting trainer must still be able to run when Gazebo validation is unavailable.

---

## 8. Exit Criteria

The validation layer is useful when:

- a trained checkpoint can be evaluated headlessly in Gazebo + ROS 2;
- scenarios produce deterministic-enough pass/fail artifacts;
- failures identify integration problems, not just "policy bad";
- the robusting layer can optionally gate checkpoint promotion on validation results.

---

## NET

Gazebo + ROS 2 is the validation and integration layer. It should test the trained
policy under ROS message flow, sensors, controllers, timing, and simulator assumptions.
It may feed the robusting layer through deterministic checkpoint gates and later
curriculum feedback, but it should not become the default RL collection loop.
