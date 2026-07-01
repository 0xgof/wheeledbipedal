# Plan - Validation and Evaluation Registry

> Defines how deterministic evaluation, robusting evaluation, Gazebo validation, and
> later hardware trials are stored and queried.

---

## 1. Goal

Store evaluation results as first-class records attached to controller candidates.

Training metrics alone are not enough. A candidate becomes meaningful only when it is
evaluated against named scenarios and thresholds.

---

## 2. Evaluation Record

Minimum record:

```yaml
candidate_id: cand_...
checkpoint_id: checkpoint_000200
evaluation_id: eval_...
validation_layer: foundational
scenario_id: balance_nominal_v1
seed: 123
pass: true
score: 0.91
metrics:
  survival_time_s: 20.0
  pitch_rms_rad: 0.04
failure_reason: null
artifacts:
  log: artifacts/eval/balance_nominal.jsonl
created_at: "2026-07-01T12:00:00Z"
```

---

## 3. Scenario Registry

Scenarios are versioned:

```text
balance_nominal_v1
balance_pitch_offset_v1
velocity_forward_0p3_v1
gazebo_latency_profile_v1
gazebo_slip_profile_v1
```

Each scenario defines:

- initial state;
- command sequence;
- seed;
- duration;
- pass/fail thresholds;
- metrics;
- required backend or validation layer.

---

## 4. Validation Layers

Use explicit layer names:

```text
foundational
robusting
gazebo_ros2
deployment_benchmark
hardware_trial
```

Do not compare candidates without showing which layer produced the metric.

---

## 5. Promotion Gates

Promotion gates are named sets of required scenarios.

Example:

```yaml
gate_id: balance_foundation_gate_v1
required_scenarios:
  - balance_nominal_v1
  - balance_pitch_offset_v1
minimum_score: 0.8
```

Gazebo gates are slower and optional, but when used they write the same evaluation
records.

---

## NET

Evaluation results are append-only candidate records. They must be scenario-versioned,
layer-specific, and machine-queryable.
