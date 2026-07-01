# MECH-1 - Mechanism Analysis for Reduced-DOF Solver

- Status: `Done`
- Stage: foundational layer / mechanism analysis
- Depends on: registry baseline
- Related: `FL-1`, `FL-2`, `FL-3`
- Source plan: `docs/plans/foundational_layer_plan.md`
- Goal: define the reduced-coordinate mechanism abstraction before implementing the Layer 1 solver.

## Problem

Layer 1 is not a full rigid-body linkage simulator. It is a fast reduced-order
ODE model for early RL experiments. Before implementing code, the repository needs
a compact mechanism analysis that states which coordinates are independent, which
linkage quantities are derived, which actuator inputs exist, and which states are
observable by deployment hardware versus privileged for simulation/training.

## Scope

1. Document true DOF for the foundational model.
2. Define reduced coordinates `q` and velocities `qdot`.
3. Define actuator inputs `u` for the initial 4-D command convention:
   - left hip command;
   - right hip command;
   - left wheel command;
   - right wheel command.
4. Define which closed-chain linkage quantities are derived, not independently
   actuated.
5. Define the kinematic maps needed by implementation:
   - forward map from reduced/actuator coordinates to derived leg geometry;
   - inverse map where meaningful for safe posture or height targets;
   - constraint residual `c(q)`;
   - Jacobian `J(q)`.
6. Define diagnostics required from the solver:
   - position residual norm;
   - velocity residual `J(q) @ qdot`;
   - limit violations;
   - optional Jacobian conditioning metric.
7. Separate deployable observation state from privileged training/debug state.
8. State the v1 simplifications explicitly: rigid no-spring leg, no hybrid
   lift-off/contact dynamics, no full DAE, no simulator backend dependency.

## Design Decisions

- Kinematics should use vector/matrix operations internally, but public APIs should
  remain domain-named.
- The solver should be configuration-driven for reduced-coordinate mechanisms that
  fit this abstraction, but it should not try to become a universal multibody engine.
- The first concrete configuration is the wheeled-biped linkage; generic interfaces
  should emerge from that real case.
- Jacobian and constraint residuals are internal validation and diagnostics first,
  not actor observations for the first PPO experiments.
- The mechanism model is a formal reduced-order mathematical definition of the
  Layer 1 problem, not a full-fidelity representation of every physical bar,
  bearing, compliance, and contact effect.

## Expected Runtime Flow

The RL agent should interact only with a Gymnasium-style step API. The matrix and
ODE computations stay inside the environment/backend implementation:

```text
policy action
    -> action adapter
    -> actuator/reduced input u
    -> kinematic maps and dynamics equations
    -> numerical integration step
    -> new reduced state
    -> derived linkage geometry
    -> observation builder
    -> policy observation
```

The agent applies actions and receives observations. It does not directly solve
constraints or manipulate raw matrices.

## Deliverable

- `docs/analysis/mechanism_dof.md`

## Acceptance

- The document defines the Layer 1 state vector and each element's domain meaning.
- The document defines actuator inputs and confirms there is no knee action.
- The document identifies independent coordinates versus derived linkage quantities.
- The document defines expected kinematic maps, residuals, and Jacobian diagnostics.
- The document defines deployable versus privileged state.
- The document gives `FL-1` enough detail to implement tests before code.

## Validation

- Documentation-only ticket; TDD is not required.
- Validate by checking that `FL-1` can derive concrete tests from the analysis
  without inventing new mechanism assumptions.
