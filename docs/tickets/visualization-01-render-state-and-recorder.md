# VIS-1 - RenderState and Trajectory Recorder

- Status: `Done`
- Stage: visualization / shared state and recording
- Depends on: `FL-1`
- Related: `VIS-2`, `VIS-3`, `VIS-4`, `VIS-5`
- Source plan: `docs/plans/visualization_plan.md`
- Goal: create the backend-neutral visualization state and recording path without adding ROS 2 or viewer dependencies to Layer 1.

## Problem

Layer 1 needs a way to inspect rollouts and mechanism diagnostics, but the solver and
Gymnasium environment must stay free of RViz, Matplotlib, Pygame, and ROS-specific
logic. Visualization needs a stable frame format that later backends can also emit.

## Scope

1. Define `RenderState` as the backend-neutral visualization schema.
2. Define `VisualizationFrame` for render state plus optional action, reward,
   termination, and diagnostics metadata.
3. Define a `VisualizationSink` protocol with:
   - `start(metadata)`;
   - `consume(frame)`;
   - `close()`.
4. Implement Layer 1 state-to-render conversion once `RobotState` and mechanism
   kinematics exist.
5. Implement JSONL trajectory recording.
6. Implement replay loading from recorded JSONL.
7. Keep the core schema serializable and independent of optional viewer packages.

## Non-goals

- RViz publishing.
- Matplotlib/Pygame rendering.
- Gymnasium `render()` support.
- Layer 2 backend adapters.
- reward calculation or simulation logic.

## Files

- `src/wheeled_biped_rl/visualization/render_state.py`
- `src/wheeled_biped_rl/visualization/frame.py`
- `src/wheeled_biped_rl/visualization/sinks.py`
- `src/wheeled_biped_rl/visualization/recorder.py`
- `src/wheeled_biped_rl/visualization/replay.py`
- `src/wheeled_biped_rl/visualization/adapters.py`
- `src/wheeled_biped_rl/visualization/plugins/jsonl_sink.py`
- `tests/test_visualization_render_state.py`
- `tests/test_visualization_recorder.py`

## Acceptance

- A `RenderState` frame can represent body pose, wheels, reduced leg/linkage posture,
  contact flags, and optional diagnostics.
- A `VisualizationFrame` can be serialized to JSONL and loaded back deterministically.
- A JSONL sink can record a short Layer 1 trajectory without ROS 2 installed.
- Adding a new sink does not require changes to solver code.
- The solver and Gym environment do not import concrete visualization plug-ins.

## Validation

- TDD required for implementation.
- Initial test run must fail before implementation for missing visualization schemas
  and recorder behavior.
- Final validation:
  - `pytest tests/test_visualization_render_state.py tests/test_visualization_recorder.py`
- Broader validation:
  - `python -m compileall -q src tests`
