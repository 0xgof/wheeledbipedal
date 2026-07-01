# VIS-4 - Layer 2 Backend Visualization Adapters

- Status: `TODO`
- Stage: visualization / robusting backend adapters
- Depends on: `VIS-1`, first selected Layer 2 backend feasibility result
- Related: robusting backend tickets, `VIS-5`
- Source plan: `docs/plans/visualization_plan.md`
- Goal: allow MuJoCo, Brax/MJX, Isaac, or another robusting backend to emit the same visualization frames as Layer 1.

## Problem

Layer 2 will use richer simulator states. Without adapters, each backend will need its
own viewer path, making cross-backend comparison harder and adding friction to training
debugging.

## Scope

1. Define adapter behavior for the first selected Layer 2 backend.
2. Convert backend-specific state into `RobotState` or directly into `RenderState`.
3. Preserve mechanism diagnostics where available.
4. Record trajectories through the existing recorder.
5. Support side-by-side or sequential comparison with Layer 1 trajectories.

## Non-goals

- choosing the robusting backend.
- implementing MuJoCo/Brax/Isaac physics.
- changing the `RenderState` schema unless the current schema is proven insufficient.
- RViz-specific changes unless needed through the existing sink.

## Files

- `src/wheeled_biped_rl/visualization/adapters.py`
- backend-specific adapter file only when a backend exists
- `tests/test_visualization_backend_adapters.py`

## Acceptance

- A Layer 2 backend trajectory can be recorded with the same recorder contract.
- Adapter code is backend-specific but viewer-independent.
- Existing sinks can consume Layer 2 frames without knowing the backend.
- Schema changes, if needed, are backwards-compatible or explicitly versioned.

## Validation

- TDD required once the first backend exists.
- Initial test run must fail before implementation for missing adapter behavior.
- Final validation:
  - `pytest tests/test_visualization_backend_adapters.py`
  - backend-specific smoke test for a short recorded rollout.
