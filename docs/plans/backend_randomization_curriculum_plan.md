# Plan - Backend, Randomization, and Curriculum Versioning

> Defines how simulator/backend assumptions, domain randomization, and curriculum stages
> are recorded for controller candidates.

---

## 1. Goal

Make training environment assumptions queryable and reproducible.

The same policy architecture and reward can behave differently under:

- Python reduced dynamics;
- MuJoCo;
- Brax/MJX;
- Isaac;
- Gazebo validation;
- different randomization profiles;
- different curriculum stages.

---

## 2. Backend Records

Each candidate records:

```yaml
backend:
  backend_id: python_sim_v1
  simulator: python_sim
  backend_version: v1
  device: cpu
  timestep_s: 0.002
  control_period_s: 0.02
  deterministic: true
```

For HPC/GPU backends also record:

- device type;
- driver/runtime versions when available;
- job id;
- node class;
- CPU/GPU count;
- wall-time limit.

---

## 3. Domain Randomization Records

Each candidate records:

```yaml
domain_randomization:
  profile_id: dr_none_v1
  enabled: false
  config_hash: "<sha256>"
```

When enabled, snapshot:

- mass/inertia ranges;
- COM offsets;
- friction/slip ranges;
- sensor noise/delay;
- actuator delay/saturation;
- timing jitter;
- randomization schedule.

---

## 4. Curriculum Records

Each candidate records:

```yaml
curriculum:
  curriculum_id: balance_curriculum_v1
  stage: 2
  promotion_rule: survival_time_and_pitch_rms
```

Curriculum changes that affect comparability should create a new id.

---

## 5. Query Use Cases

The registry should answer:

- best candidate trained on `python_sim_v1`;
- candidates trained with friction randomization enabled;
- candidates from curriculum stage 3;
- checkpoints that passed Gazebo after Isaac training;
- candidates trainable on CPU only.

---

## NET

Backend, randomization, and curriculum are not incidental run settings. They are
candidate-defining assumptions and must be snapshotted.
