# VIS-2 - RViz Sink for Layer 1 Replay

- Status: `TODO`
- Stage: visualization / RViz adapter
- Depends on: `VIS-1`, ROS 2 description package
- Related: `VIS-3`, `VIS-5`
- Source plan: `docs/plans/visualization_plan.md`
- Goal: make RViz consume recorded or live `RenderState` frames through a plug-in sink without coupling RViz to the solver or Gym environment.

## Problem

RViz is useful as the main robotics viewer, but it must remain a visualization plug-in.
The Layer 1 environment should not publish ROS messages or know that RViz exists.

## Scope

1. Implement an `RvizSink` or ROS 2 replay node that consumes `VisualizationFrame`
   or `RenderState`.
2. Publish robot pose through `/joint_states` and `/tf`.
3. Publish optional markers for:
   - contacts;
   - center of mass;
   - constraint residuals;
   - velocity residuals;
   - target/reference geometry.
4. Provide a launch file or documented command for replaying a recorded trajectory.
5. Keep ROS imports isolated behind the RViz plug-in.

## Non-goals

- Gazebo physics.
- PPO training integration.
- changing `WheeledBipedEnv.step`.
- making RViz a required dependency for Layer 1.
- validating physics accuracy.

## Files

- `src/wheeled_biped_rl/visualization/plugins/rviz_sink.py`
- `src/wheeled_biped_rl/ros2/` files only if shared ROS helpers are needed
- `ros2_ws/src/wheeled_biped_description/launch/` replay launch files if needed
- `tests/test_visualization_rviz_sink.py` for import-guarded/unit-level behavior

## Acceptance

- RViz-specific code is isolated behind the plug-in boundary.
- Non-ROS installs can import the visualization core without failure.
- Recorded Layer 1 frames can be replayed into RViz when ROS 2 is available.
- `/joint_states` and `/tf` mapping is documented and deterministic.
- Optional markers are derived from diagnostics, not from simulator-specific internals.

## Validation

- TDD required for import guards and state-to-message mapping where practical.
- Initial test run must fail before implementation for missing RViz sink behavior.
- Final local validation:
  - `pytest tests/test_visualization_rviz_sink.py`
  - `python -m compileall -q src tests`
- Manual ROS validation, when ROS 2 is available:
  - replay a recorded trajectory into RViz and confirm joint frames and markers update.
