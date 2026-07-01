# Visualization Plan

> Companion to [`repo_structure_plan.md`](repo_structure_plan.md),
> [`foundational_layer_plan.md`](foundational_layer_plan.md), and
> [`ros2_rviz_display_plan.md`](ros2_rviz_display_plan.md).

This plan defines visualization as a shared debugging and validation surface for
Layer 1, later robusting backends, and ROS 2/Gazebo validation. RViz is one preferred
human-facing robotics viewer, but visualization must be a pluggable adapter system.
It must not own simulation, training, or reward logic.

---

## 1. Goal

Create a visualization path that makes rollouts understandable without coupling the
fast RL loop to ROS 2.

The visualization system should show:

- robot body pose and pitch;
- wheel positions and rotations;
- reduced leg/linkage posture;
- contact flags;
- center of mass or simplified mass marker when available;
- actions, reward components, and mechanism diagnostics during replay;
- constraint and Jacobian residuals for debugging the reduced solver.

---

## 2. Core Principle

Visualization consumes state. It does not simulate.

```text
backend-specific state
    -> state adapter
    -> RobotState / RenderState
    -> visualization dispatcher
    -> recorder / RViz / local renderer / future viewers
```

Layer 1, MuJoCo, Brax/MJX, Isaac, Gazebo, and real-robot logs should all be able to
map into a common renderable state shape when practical.

---

## 3. Target Flow

```text
Layer 1 solver
    -> RobotState
    -> RenderState
    -> trajectory recorder
    -> local replay / RViz bridge / videos

Layer 2 backend
    -> backend state adapter
    -> RobotState or RenderState
    -> same recorder and visualizers

ROS 2 / Gazebo validation
    -> /joint_states, /tf, markers, metrics
    -> RViz and recorded validation artifacts
```

The training loop should remain Gymnasium-compatible and ROS-free:

```text
env.step(action)
    -> observation, reward, terminated, truncated, info
```

Any visualization side effects should be optional, disabled by default during high
throughput training, and driven by recorded state or explicit debug runs.

---

## 4. Plug-in Architecture

The Gymnasium environment should not know about RViz, Matplotlib, Pygame, rerun.io,
MeshCat, or any future viewer. It should expose state and optional render data through
a narrow interface.

```text
WheeledBipedEnv / backend
    -> RobotState
    -> RenderState
    -> VisualizationSink protocol
    -> concrete sink:
         - JsonlTrajectorySink
         - RvizSink
         - MatplotlibSink
         - PygameSink
         - TensorBoardVideoSink
         - future sink
```

The core contract is:

```text
start(metadata)
consume(frame)
close()
```

Where `frame` is a serializable visualization frame containing `RenderState` and
optional action, reward, termination, and diagnostic metadata.

### 4.1 Adapter Boundary

Use two adapter types:

- **State adapters** convert backend-specific state into `RobotState` or `RenderState`.
- **Viewer sinks** consume `RenderState` frames and send them to storage or a display.

This keeps friction out of the Gym environment:

- the environment does not publish ROS messages;
- the solver does not import visualization code;
- RViz-specific code stays behind the `RvizSink`;
- another viewer can be plugged in by implementing the same sink protocol.

### 4.2 Configuration

Visualization should be selected by config or CLI, not hard-coded:

```yaml
visualization:
  enabled: true
  sinks:
    - type: jsonl
      path: runs/latest/trajectory.jsonl
    - type: rviz
      enabled: false
    - type: rgb_array
      enabled: false
```

Training defaults should keep visualization disabled except for lightweight recording
or explicitly requested debug rollouts.

---

## 5. Components

### 5.1 `RenderState`

`RenderState` is the backend-neutral visualization schema.

It should include:

- timestamp or step index;
- body pose in a simple world frame;
- body dimensions or visual primitive identifier;
- wheel poses and radii;
- leg/linkage keypoints or derived joint poses;
- contact flags;
- optional COM marker;
- optional action vector;
- optional reward and termination metadata;
- optional diagnostics such as position residual, velocity residual, and limit status.

`RenderState` should be derivable from `RobotState` plus mechanism kinematics. It should
not replace `RobotState`.

### 5.2 Trajectory Recorder

The recorder persists rollout frames for replay and comparison.

Initial storage can be JSONL because it is inspectable and easy to diff:

```text
step, time_s, action, observation_summary, reward, RobotState, RenderState, diagnostics
```

Later, NPZ or Parquet can be added if throughput or file size becomes a real problem.

### 5.3 RViz Bridge

RViz is the preferred robotics viewer.

The RViz plug-in should consume `RenderState` or `RobotState` and publish:

- `/joint_states`;
- `/tf`;
- optional marker arrays for COM, contacts, constraint residuals, planned targets, and
  debug geometry.

RViz should not be required for training. It is a debug/replay/validation sink.

### 5.4 Local Renderer

A lightweight local renderer remains useful even if RViz is the main viewer.

Acceptable first options:

- Matplotlib animation for simple 2D debugging and saved videos;
- Pygame for interactive local playback;
- Gymnasium `render_mode="rgb_array"` for tool compatibility.

This renderer can be minimal and implemented after the state/recorder path exists.

### 5.5 Training Dashboards

Training metrics should use standard RL tooling:

- TensorBoard first for reward components, losses, episode length, success rate, and
  optional rollout videos;
- optional W&B or MLflow later if local registry artifacts need a commercial or
  standard tracking backend.

---

## 6. Build Order

### VIS-1 - RenderState and Trajectory Recorder

Build after `FL-1` has a stable `RobotState` and mechanism kinematics.

Deliver:

- `RenderState` dataclass or equivalent schema;
- `VisualizationFrame` schema for state plus optional action/reward/diagnostics;
- `VisualizationSink` protocol;
- conversion from Layer 1 state to `RenderState`;
- JSONL trajectory recorder;
- replay loader;
- tests for schema stability and deterministic serialization.

### VIS-2 - RViz Bridge for Layer 1 Replay

Build after `VIS-1` and after the ROS description can represent the simplified robot.

Deliver:

- `RvizSink` or ROS 2 node/script that replays recorded `RenderState`;
- `/joint_states` and `/tf` publication;
- optional markers for contacts and diagnostics;
- launch file or documented command for RViz replay.

### VIS-3 - Gymnasium Render and Local Viewer

Build after `FL-2`.

Deliver:

- `render_mode="rgb_array"` support for `WheeledBipedEnv`;
- optional Matplotlib/Pygame human viewer;
- saved rollout video path for short debug runs.

### VIS-4 - Layer 2 Backend Adapters

Build only when a robusting backend exists.

Deliver:

- adapter from MuJoCo, Brax/MJX, or Isaac state to `RenderState`;
- comparison replay between Layer 1 and Layer 2 trajectories;
- recorded diagnostics for backend mismatch.

### VIS-5 - Gazebo Validation Replay

Build with the Gazebo validation layer.

Deliver:

- recorded Gazebo/ROS validation trajectories;
- RViz replay of validation runs;
- machine-readable alignment between checkpoint, scenario, metrics, and rendered
  trajectory.

---

## 7. Repository Shape

Create only when needed:

```text
src/wheeled_biped_rl/
    visualization/
        __init__.py
        render_state.py
        frame.py
        sinks.py
        recorder.py
        replay.py
        adapters.py
        plugins/
            __init__.py
            jsonl_sink.py
            rviz_sink.py
            gym_render_sink.py
```

Avoid putting visualization logic inside `simulation/`, `envs/`, or `training/`.

Expected dependency direction:

```text
visualization core    -> standard-library dataclasses/protocols where possible
visualization adapters -> simulation / envs kinematic outputs
visualization plugins  -> optional external dependencies
training              -> optional sink hook only
ros2                  -> optional RViz plug-in integration
```

The solver must not import the visualizer.

---

## 8. Non-goals

- No physics in visualization.
- No reward calculation in visualization.
- No required ROS 2 dependency for Layer 1 training.
- No Gazebo dependency for the first viewer.
- No attempt to make RViz an RL environment step factory.
- No hard dependency on any single viewer.
- No viewer-specific branches inside `WheeledBipedEnv.step`.

---

## 9. Acceptance Criteria

- A Layer 1 rollout can be recorded without ROS 2 installed.
- The same recorded rollout can be replayed into RViz when ROS 2 is available.
- Visualization can display mechanism diagnostics without exposing them as required
  actor observations.
- The local training loop can run with visualization disabled.
- The design can accept Layer 2 backend states through adapters without changing the
  recorder schema unnecessarily.
- RViz can be removed or replaced without changing the Gym environment or solver.
- Adding a new viewer requires a new sink/adapter, not changes to environment stepping.
