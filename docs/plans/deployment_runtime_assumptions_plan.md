# Plan - Deployment and Runtime Assumptions

> Defines the runtime assumptions that make a trained controller deployable or not.

---

## 1. Goal

Record the assumptions required to run a controller candidate outside training.

A checkpoint is not deployable unless its runtime interface, timing, safety, and export
constraints are known.

---

## 2. Runtime Profile

Each deployment candidate records:

```yaml
runtime:
  runtime_profile_id: raspberry_pi_runtime_v1
  export_format: onnx
  policy_frequency_hz: 50
  observation_interface_id: actor_obs_balance_v1
  action_interface_id: hip_wheel_4d_v1
  safety_profile_id: safety_limits_v1
  normalization_snapshot: normalization.yaml
```

---

## 3. Timing Assumptions

Record:

- policy frequency;
- sensor frequency;
- controller frequency;
- maximum allowed inference time;
- p95/p99 measured inference time;
- action delay assumptions;
- observation delay assumptions.

---

## 4. Safety Assumptions

Record:

- joint limits;
- wheel speed limits;
- torque/current limits;
- pitch/roll cutoffs;
- emergency stop behavior;
- timeout behavior;
- manual override assumptions.

---

## 5. Export Artifacts

Track:

- source checkpoint;
- export format;
- export command;
- model size;
- runtime dependencies;
- benchmark result;
- compatibility status.

---

## NET

Deployment assumptions are part of the controller candidate. A candidate without runtime
profile, safety profile, and export metadata is not a deployment candidate.
