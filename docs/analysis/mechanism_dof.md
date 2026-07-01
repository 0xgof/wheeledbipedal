# Mechanism DOF Analysis

Layer 1 uses a formal reduced-order model, not a full closed-chain DAE or a
general-purpose multibody engine.

## First Model

- Mechanism id: `kollarcik_2021_rigid_v1`
- Source: `configs/robot/wheeled_biped.yaml`, grounded in `docs/robot/robot_description.md`
- Topology: Ascento-class closed-chain wheeled biped
- Simplification: rigid no-spring leg
- Excluded from v1: full DAE loop closure, spring compliance, lift-off/contact switching,
  Gazebo/MuJoCo/Isaac/Brax backend dependencies

## Reduced Coordinates

```text
q = [
  body_pitch_rad,
  body_x_m,
  body_z_m,
  left_hip_rad,
  right_hip_rad,
  left_wheel_rad,
  right_wheel_rad
]

qdot = [
  body_pitch_rad_s,
  body_x_m_s,
  body_z_m_s,
  left_hip_rad_s,
  right_hip_rad_s,
  left_wheel_rad_s,
  right_wheel_rad_s
]
```

## Actuator Inputs

```text
u = [
  left_hip,
  right_hip,
  left_wheel,
  right_wheel
]
```

There is no knee action. The knee/linkage state is derived from the reduced mechanism
model.

## Kinematic Contract

Layer 1 exposes domain-named outputs while using vector-style math internally:

- forward map: reduced hip state to derived leg geometry
- inverse height map: reachable leg height to hip command
- position residual: `c(q)`
- velocity residual: `J(q) @ qdot`
- diagnostics: residual norms, limit status, optional Jacobian conditioning

The first implementation uses a rigid effective leg length:

```text
leg_length = l1 + l3
```

This is intentionally simpler than the thesis DAE and exists to prove the RL
formulation cheaply before robusting backends are introduced.

## Observability Split

Deployable actor observation should be based on measurable fields:

- motor positions
- motor velocities
- motor torques
- IMU pitch/roll
- IMU rates

Privileged/debug state may include:

- full derived linkage state
- exact body velocity
- contact forces
- constraint residuals

Residual diagnostics are for tests, debugging, and possible critic/debug use. They are
not required actor observations for the first PPO experiments.
