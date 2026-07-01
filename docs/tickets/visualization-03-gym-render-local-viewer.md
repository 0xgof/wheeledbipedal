# VIS-3 - Gymnasium Render and Local Viewer

- Status: `TODO`
- Stage: visualization / Gymnasium compatibility
- Depends on: `VIS-1`, `FL-2`
- Related: `VIS-2`
- Source plan: `docs/plans/visualization_plan.md`
- Goal: add lightweight Gymnasium-compatible rendering without hard-coding a viewer into the environment step path.

## Problem

RL tooling expects environments to support render modes such as `rgb_array`, but the
environment should still avoid viewer-specific branches and ROS dependencies.

## Scope

1. Add `render_mode="rgb_array"` support to `WheeledBipedEnv`.
2. Use `RenderState` and visualization sinks rather than duplicating state conversion.
3. Provide a minimal local renderer, likely Matplotlib first or Pygame if interaction is
   needed.
4. Allow short rollout videos to be saved for debugging and training logs.
5. Keep high-throughput training defaulting to no rendering.

## Non-goals

- RViz implementation.
- replacing the trajectory recorder.
- heavy 3D rendering.
- simulator physics validation.

## Files

- `src/wheeled_biped_rl/visualization/plugins/gym_render_sink.py`
- `src/wheeled_biped_rl/visualization/plugins/matplotlib_sink.py` or equivalent only if chosen
- `src/wheeled_biped_rl/envs/wheeled_biped_env.py`
- `tests/test_env_render.py`
- `tests/test_visualization_local_render.py`

## Acceptance

- `WheeledBipedEnv` can return an `rgb_array` frame when configured for that mode.
- Rendering is disabled by default.
- The environment does not contain RViz-specific or Matplotlib-specific logic.
- A short rollout can produce deterministic frame dimensions.
- Rendering consumes `RenderState`, not raw simulator internals.

## Validation

- TDD required.
- Initial test run must fail before implementation for missing render behavior.
- Final validation:
  - `pytest tests/test_env_render.py tests/test_visualization_local_render.py`
  - `python -m compileall -q src tests`
