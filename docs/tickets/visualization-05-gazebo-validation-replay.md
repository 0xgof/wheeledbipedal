# VIS-5 - Gazebo Validation Replay

- Status: `TODO`
- Stage: visualization / Gazebo and validation replay
- Depends on: `VIS-1`, `VIS-2`, Gazebo validation layer
- Related: `VIS-4`, Gazebo validation feedback tickets
- Source plan: `docs/plans/visualization_plan.md`
- Goal: record and replay Gazebo/ROS validation runs through the same visualization and artifact path used by earlier layers.

## Problem

Gazebo validation should produce inspectable artifacts, not only pass/fail metrics. The
visualization system should connect validation checkpoints, scenarios, metrics, and
rendered trajectories without turning Gazebo into the RL training loop.

## Scope

1. Record Gazebo/ROS validation trajectories into `VisualizationFrame` or compatible
   artifacts.
2. Replay validation trajectories into RViz.
3. Link recorded trajectories to:
   - controller candidate id;
   - checkpoint id;
   - scenario id;
   - validation metrics;
   - backend metadata.
4. Preserve timing and latency metadata when available.
5. Keep Gazebo validation outside the PPO/SAC collection loop.

## Non-goals

- primary RL training inside Gazebo.
- changing the controller candidate registry schema unless a real artifact reference
  is needed.
- replacing Gazebo metrics with visual inspection.
- making ROS 2 a required dependency for Layer 1 or Layer 2 training.

## Files

- `src/wheeled_biped_rl/validation/gazebo_runner.py`
- `src/wheeled_biped_rl/validation/metrics.py`
- `src/wheeled_biped_rl/visualization/plugins/rviz_sink.py`
- registry artifact references only if needed
- validation tests once Gazebo integration exists

## Acceptance

- A Gazebo validation run can emit a replayable visualization artifact.
- The artifact is linked to the candidate/checkpoint/scenario it validates.
- RViz replay uses the existing plug-in path.
- Training remains able to run without ROS 2/Gazebo installed.

## Validation

- TDD required for artifact metadata and replay parsing where practical.
- Final validation depends on Gazebo availability:
  - unit tests for metadata/replay parsing;
  - manual or CI Gazebo replay check when the validation layer exists.
