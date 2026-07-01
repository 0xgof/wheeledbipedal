# Plan - Robot and Mechanism Versioning

> Defines how robot configuration and reduced/full mechanism assumptions are versioned
> inside controller candidates.

---

## 1. Goal

Make robot and mechanism assumptions explicit.

A policy trained against one mechanism model may not be compatible with another, even if
the neural network shape is unchanged.

---

## 2. Versioned Inputs

Track:

- canonical robot config path and `meta.config_version`;
- robot config content hash;
- mechanism model id;
- reduced-coordinate definition;
- constrained-linkage assumptions;
- actuator mapping assumptions;
- spring/contact mode settings;
- physical parameter calibration source.

Example ids:

```text
robot_config_wheeled_biped_v1
mechanism_rigid_no_spring_v1
mechanism_sprung_linkage_v1
mechanism_contact_switching_v1
```

---

## 3. Candidate Manifest Fields

```yaml
robot:
  config_id: robot_config_wheeled_biped_v1
  config_version: 1
  config_hash: "<sha256>"
  source_path: configs/robot/wheeled_biped.yaml

mechanism:
  mechanism_id: mechanism_rigid_no_spring_v1
  reduced_coordinates: hip_wheel_per_side_v1
  knee_actuated: false
  spring_enabled: false
  contact_model: grounded_v1
```

---

## 4. Compatibility Rules

Candidates are incompatible by default when:

- `mechanism_id` differs;
- action actuator mapping differs;
- robot dimensions or limits differ materially;
- spring/contact mode changes;
- observation fields depend on removed or newly privileged state.

Comparison tooling should report these mismatches explicitly.

---

## 5. Required Artifacts

Each candidate snapshots:

- robot config;
- mechanism spec;
- kinematics/dynamics model id;
- calibration notes if available.

---

## NET

Robot and mechanism assumptions are first-class candidate metadata. Do not rely on file
names or memory to know which linkage model produced a checkpoint.
