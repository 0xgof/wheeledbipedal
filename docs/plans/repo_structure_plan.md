# Repository Structure Plan — Wheeled-Biped RL

> Companion to [`docs/goal/wheeled_biped_rl_architecture.md`](../goal/wheeled_biped_rl_architecture.md).
> This document defines the **concrete repository layout**, the responsibility of each
> module, the dependency boundaries between layers, and the order in which the
> structure should be built out. It is a structural plan, not an algorithm design doc.

---

## 1. Guiding structural principles

These rules drive every decision below. If a future change violates one of them,
the change is probably wrong.

1. **The RL layer never imports ROS 2.** Training code depends only on the
   Gymnasium environment interface and the `BaseBackend` protocol.
2. **One direction of dependencies.** `training → envs → backends → simulation`.
   Lower layers never import higher layers. `utils` is leaf-level and may be
   imported by anyone.
3. **Train/deploy parity.** `ObservationBuilder`, `ActionAdapter`, normalization,
   and `SafetySupervisor` are written **once** and reused by both the training env
   and the deployment node. They live in shared modules, never duplicated.
4. **Config over code.** Behaviours, randomization, and algorithm hyperparameters
   are YAML files, not hard-coded constants in training scripts.
5. **Deployable vs privileged state is explicit.** The observation builder must be
   able to produce an actor observation (Raspberry-Pi-realistic) separately from a
   critic/privileged observation.
6. **Build the smallest thing that runs first.** The directory tree below is the
   *target*; Section 6 defines what actually gets created in each phase. Do not
   scaffold empty packages ahead of need.

---

## 2. Top-level layout

```text
wheeledbipedal/
├── README.md
├── pyproject.toml                # packaging, deps, tool config (ruff/black/pytest)
├── .gitignore
├── .python-version               # pinned interpreter (optional)
│
├── docs/
│   ├── goal/
│   │   └── wheeled_biped_rl_architecture.md
│   ├── robot/
│   │   └── robot_description.md     # concrete robot (Ascento-class, thesis-grounded)
│   └── plans/
│       └── repo_structure_plan.md   # (this file)
│
├── configs/                      # all YAML; no logic here
├── src/
│   └── wheeled_biped_rl/         # the importable Python package
├── scripts/                      # thin CLI entry points → call into src/
├── hpc/                          # scheduler/job templates for remote training
├── ros2_ws/                      # ROS 2 workspace (validation/deployment, kept separate)
└── tests/
```

**Why `src/` layout:** prevents accidental imports of the package from the repo
root and forces an installed-package workflow (`pip install -e .`), which is the
same way it will be imported on the Pi. The ROS 2 workspace is deliberately a
sibling tree (`ros2_ws/`), not inside the Python package, because it is built with
`colcon`, not `pip`.

---

## 3. The Python package (`src/wheeled_biped_rl/`)

Each sub-package below is a dependency layer. The arrows in Section 4 show what may
import what.

```text
src/wheeled_biped_rl/
├── __init__.py
│
├── envs/                         # RL-specific logic (Gymnasium API surface)
│   ├── __init__.py
│   ├── wheeled_biped_env.py      # WheeledBipedEnv(gym.Env): reset/step orchestration
│   ├── observation_builder.py    # RobotState -> obs vector; actor vs privileged (uses leg_kinematics fwd map)
│   ├── reward_builder.py         # per-component rewards, returns dict + scalar
│   ├── action_adapter.py         # [-1,1] -> physical refs; clip/smooth/rate-limit (uses leg_kinematics inv map)
│   ├── leg_kinematics.py         # closed-chain motor↔joint map + Jacobian (pure geometry; shared w/ deployment)
│   └── termination.py            # has_fallen / has_timed_out
│
├── backends/                     # execution abstraction (no RL logic)
│   ├── __init__.py
│   ├── base_backend.py           # BaseBackend Protocol: reset/step/close
│   ├── python_sim_backend.py     # wraps simulation/ for fast training
│   ├── mujoco_backend.py         # robusting candidate, added only if selected/proven
│   ├── brax_mjx_backend.py       # robusting candidate, added only if selected/proven
│   ├── isaac_backend.py          # robusting candidate, added only if selected/proven
│   ├── ros2_gazebo_backend.py    # validation/integration backend
│   └── real_robot_backend.py     # real robot evaluation
│
├── simulation/                   # pure physics; knows nothing about RL or gym
│   ├── __init__.py
│   ├── robot_state.py            # RobotState (+ vertical pos/vel, per-wheel contact flags) + RobotAction
│   ├── simple_dynamics.py        # planar EoM; v1 = rigid no-spring leg; optional spring + contact-mode (config-gated)
│   └── integration.py            # integrators (semi-implicit Euler / RK4)
│
├── real_world_effects/           # deployment-realism wrappers (Phase 3+)
│   ├── __init__.py
│   ├── sensor_model.py           # noise / bias / drift / quantization / dropout
│   ├── actuator_model.py         # saturation, time constant, voltage derate
│   ├── delay_model.py            # observation & action delay buffers
│   ├── domain_randomizer.py      # samples mass/COM/friction per episode
│   └── real_world_wrapper.py     # gym.Wrapper composing the models above
│
├── policies/                     # network defs + export
│   ├── __init__.py
│   ├── networks.py               # compact MLP actor/critic (64-64 / 128-128); asymmetric (privileged critic) supported
│   └── export.py                 # state_dict / TorchScript / ONNX export
│
├── training/                     # Tianshou glue (imports everything below it)
│   ├── __init__.py
│   ├── env_factory.py            # build_env(config) -> vectorized envs
│   ├── backend_factory.py        # choose Python/MuJoCo/Brax/Isaac adapter from config
│   ├── train_ppo.py              # PPO trainer assembly
│   ├── train_sac.py              # SAC trainer assembly (Phase 2+)
│   ├── collectors.py             # train/test collector construction
│   ├── checkpoint_gates.py       # optional deterministic eval / Gazebo validation gates
│   └── logging.py                # reward-component + metric logging (TB/CSV/JSONL)
│
├── validation/                   # validation runners outside the RL collection loop
│   ├── __init__.py
│   ├── scenarios.py              # deterministic scenario definitions
│   ├── gazebo_runner.py          # submit/run Gazebo validation for exported checkpoints
│   └── metrics.py                # validation result parsing and scoring
│
├── safety/                       # shared by training-sim and real deployment
│   ├── __init__.py
│   ├── safety_supervisor.py      # filter(action, state) -> safe action + flags
│   └── limits.py                 # limit dataclasses loaded from safety YAML
│
├── ros2/                         # ROS 2 deployment node (Phase 5; import-guarded)
│   ├── __init__.py
│   ├── policy_node.py
│   ├── ros2_interface.py
│   └── message_adapters.py
│
├── deployment/                   # Raspberry Pi runtime + benchmarking
│   ├── __init__.py
│   ├── inference_runtime.py      # load exported model, run obs->action loop
│   ├── raspberry_pi_node.py
│   └── benchmark_policy.py       # inference latency / deadline-miss report
│
└── utils/                        # leaf-level helpers (no internal deps)
    ├── __init__.py
    ├── config.py                 # YAML load + schema/dataclass binding
    ├── seeding.py                # deterministic seeding helpers
    └── math_utils.py             # projected gravity, quat/euler, clamps
```

### 3.1 Module responsibility summary

| Module | Owns | Must NOT do |
|---|---|---|
| `envs/` | obs build, reward, termination, action adapt, episode bookkeeping | physics, ROS 2, network defs |
| `backends/` | reset/step execution, return `RobotState` | reward, obs vector, RL concepts |
| `simulation/` | equations of motion, state dataclasses, integration | gym, Tianshou, ROS 2 |
| `real_world_effects/` | sensor/actuator imperfection + randomization | physics truth, reward |
| `policies/` | network architecture, export formats | env, training loop |
| `training/` | Tianshou assembly, collectors, backend selection, checkpoint gates, logging | physics, ROS 2 internals |
| `validation/` | deterministic validation scenarios, Gazebo result ingestion, checkpoint scoring | PPO/SAC collection, policy training updates |
| `safety/` | hard limits enforced at runtime | learning, simulation |
| `ros2/` | topic I/O, message<->RobotState mapping | reward, training |
| `deployment/` | embedded inference + benchmarking | training, simulation |
| `utils/` | pure helpers | importing any sibling package |

### 3.2 Robot-specific module notes

These follow from the concrete robot — see
[`docs/robot/robot_description.md`](../robot/robot_description.md) (Ascento-class,
closed-chain legs, optional sprung passive knee, diff-drive; grounded in the
Kollarčík 2021 CTU thesis).

- **`leg_kinematics` is mandatory and bidirectional.** Forward map (motor encoders →
  joint/leg state) feeds `observation_builder`; inverse map (policy target → motor
  refs) feeds `action_adapter`; both reuse the *same* module on the real robot
  (train/deploy parity). Its test must assert `forward∘inverse = identity`.
- **Optional torsion spring + contact mode are config-gated.** v1 runs a **rigid,
  no-spring** leg (2-DOF/side: wheel + hip-set leg length). `simple_dynamics` adds the
  spring potential term and the lift-off/contact mode **only when enabled** — never
  baked in. `RobotState` carries vertical state + contact flags from the start so
  jumping needs no later refactor.
- **Asymmetric actor-critic (Phase 3+).** `observation_builder` emits an actor
  (deployable) view and a privileged (sim-only: true velocity, COM, friction, payload,
  contact forces) view; `training/` routes the privileged view to the **critic only**.
  The actor additionally needs a short observation **history** (frame-stack/recurrence)
  to infer hidden state (e.g. velocity) under partial observability — on the real robot
  encoders give only *sums* of some joint angles.

---

## 4. Dependency boundaries

```text
            scripts/  ───────────────┐
                                      ▼
                                  training/
                                      │
                 ┌────────────────────┼───────────────┐
                 ▼                    ▼                ▼
             policies/             envs/          (logging)
                                     │
                        ┌────────────┼─────────────┐
                        ▼            ▼              ▼
                 real_world_effects backends/    safety/
                                     │
                                     ▼
                                simulation/

   utils/  ◄── importable by every layer (leaf, no internal imports)
   deployment/ , ros2/  ── import: policies(export), safety, envs(builders), utils
```

Enforcement idea (optional, cheap): an `import-linter` contract in `pyproject.toml`
that fails CI if `envs`/`training` import `ros2`, or if `simulation` imports `gym`.

---

## 5. Config tree (`configs/`)

YAML only. Mirrors the architecture doc, grouped by concern so a single training run
composes one file from each relevant group.

```text
configs/
├── tasks/                        # behaviour definitions (command/reward/term/curriculum)
│   ├── stand_balance.yaml
│   ├── velocity_tracking.yaml
│   ├── curved_path_tracking.yaml
│   ├── payload_randomized_balance.yaml
│   ├── disturbance_recovery.yaml
│   ├── one_wheel_balance.yaml    # specialist (contact-switching)
│   └── jump.yaml                 # specialist (contact-switching); later phase
├── env/
│   ├── balance.yaml
│   ├── velocity_tracking.yaml
│   └── ros2_gazebo.yaml
├── backends/
│   ├── python_sim.yaml
│   ├── mujoco.yaml
│   ├── brax_mjx.yaml
│   ├── isaac.yaml
│   └── gazebo_validation.yaml
├── algo/
│   ├── ppo.yaml
│   └── sac.yaml
├── validation/
│   ├── gazebo_checkpoint_gate.yaml
│   ├── scenarios_nominal.yaml
│   └── scenarios_hard.yaml
├── robot/
│   ├── simplified_planar.yaml    # masses, links, wheel radius, limits (seed: thesis Table 2.1)
│   ├── leg_spring.yaml           # optional torsion spring (k, β); v1: enabled = false
│   └── robot_limits.yaml
├── real_world/
│   ├── domain_randomization.yaml # training randomization ranges
│   ├── evaluation_nominal.yaml
│   ├── evaluation_hard.yaml
│   ├── evaluation_extreme.yaml
│   └── deployment_pi.yaml
└── safety/
    └── safety_limits.yaml
```

**Composition model:** a run is specified as `task + env + algo + robot + real_world`
(+ `safety`). `utils/config.py` loads and merges them into a single typed config
object. Keep each file single-concern so profiles (e.g. `evaluation_hard`) swap
cleanly without touching task definitions.

---

## 6. Build order (which structure gets created when)

Scaffold only what each phase needs. Maps to the architecture doc's development phases.

### Phase 0 — Repo skeleton
- `pyproject.toml`, `README.md`, `.gitignore`, `src/wheeled_biped_rl/__init__.py`.
- `utils/{config,seeding,math_utils}.py`.
- `tests/` with one smoke test that imports the package.
- **Deliverable:** `pip install -e .` works; `pytest` green.

### Phase 1 — Minimal balance loop
- `simulation/{robot_state,simple_dynamics,integration}.py` — v1 = **rigid no-spring leg**
  (2-DOF/side: wheel + hip-set leg length); `RobotState` already carries vertical state +
  contact flags (unused until jumping).
- `backends/{base_backend,python_sim_backend}.py`.
- `envs/{wheeled_biped_env,observation_builder,reward_builder,action_adapter,leg_kinematics,termination}.py`.
- `policies/networks.py`; `training/{env_factory,collectors,logging,train_ppo}.py`.
- `configs/{robot/simplified_planar, env/balance, algo/ppo, tasks/stand_balance}.yaml` (robot seeded from thesis Table 2.1).
- `scripts/train_ppo.py`, `scripts/evaluate_policy.py`.
- `tests/{test_env_api,test_observation_builder,test_action_adapter,test_leg_kinematics,test_reward_builder}.py`
  — `test_leg_kinematics` must assert forward/inverse maps are exact inverses.
- **Deliverable (success criterion #1):** PPO keeps the model upright for a full episode.

### Phase 2 — Velocity tracking
- Extend `observation_builder` (command vector) + `reward_builder` (tracking term).
- `configs/{tasks/velocity_tracking, env/velocity_tracking}.yaml`; randomized commands.
- Add `training/train_sac.py` + `configs/algo/sac.yaml` once env is stable.
- **Deliverable (success criterion #2):** velocity tracking under randomized commands.

### Phase 3 — Robustness / real-world effects
- `real_world_effects/*` and `safety/{safety_supervisor,limits}.py`.
- `configs/real_world/*`, `configs/safety/safety_limits.yaml`.
- `tests/{test_real_world_effects,test_safety_supervisor}.py`.
- Introduce one effect at a time. For *this* robot the data says wheel friction/slip is
  first-order (slip at ~0.5 N·m ≪ 2 N·m ceiling), so prioritize: action delay → IMU
  noise/delay → motor saturation → **wheel friction/slip** → COM randomization → jitter.

### Phase 4 — ROS 2 / Gazebo backend
- `ros2_ws/src/wheeled_biped_description/{urdf,meshes,launch,config}`.
- `backends/ros2_gazebo_backend.py`, `ros2/{ros2_interface,message_adapters}.py`.
- `configs/env/ros2_gazebo.yaml`. ROS 2 imports are guarded so non-ROS installs still work.

### Phase 5 — Export & deployment node
- `policies/export.py`, `deployment/{inference_runtime,benchmark_policy,raspberry_pi_node}.py`.
- `ros2/policy_node.py`; `scripts/{export_policy,benchmark_policy_on_pi}.py`.

### Phase 6 — Real robot evaluation
- `backends/real_robot_backend.py`; tighten `safety/` for hardware; eval-only profiles.

### Updated layer build order

The Phase 4-6 sequence above predates the three-layer simulator strategy. Use this
updated order for new work:

#### Phase 4 - Robusting backend feasibility

- Add `training/backend_factory.py` and backend config files under `configs/backends/`.
- Add candidate backend adapters only when they are being tested:
  `backends/mujoco_backend.py`, `backends/brax_mjx_backend.py`, and/or
  `backends/isaac_backend.py`.
- Build the same minimal constrained-linkage scenario in each candidate backend.
- Add benchmark/evaluation scripts that report constraint stability, step throughput,
  reset reliability, and modelling limitations.
- Do not make Isaac or any GPU-only stack a hard dependency; keep a CPU-friendly path.

#### Phase 5 - HPC-capable robusting training

- Add `hpc/` scheduler templates and non-interactive run examples.
- Add checkpoint/resume, run metadata, resolved-config snapshots, and backend metadata.
- Add `training/checkpoint_gates.py` for deterministic local evaluation and optional
  validation gates.
- Add `validation/{scenarios,metrics}.py` for machine-readable checkpoint scoring.
- **Deliverable:** selected backend can train/fine-tune headlessly on local or HPC runs.

#### Phase 6 - ROS 2 / Gazebo validation feedback

- `ros2_ws/src/wheeled_biped_description/{urdf,meshes,launch,config}`.
- `backends/ros2_gazebo_backend.py`, `ros2/{ros2_interface,message_adapters}.py`, and
  `validation/gazebo_runner.py`.
- `configs/env/ros2_gazebo.yaml` and `configs/validation/gazebo_checkpoint_gate.yaml`.
- Gazebo validation can gate or score checkpoints, but ROS 2 imports stay guarded and
  Gazebo does not become the default PPO/SAC collection loop.

#### Phase 7 - Export & deployment node

- `policies/export.py`, `deployment/{inference_runtime,benchmark_policy,raspberry_pi_node}.py`.
- `ros2/policy_node.py`; `scripts/{export_policy,benchmark_policy_on_pi}.py`.

#### Phase 8 - Real robot evaluation

- `backends/real_robot_backend.py`; tighten `safety/` for hardware; eval-only profiles.

---

## 7. Packaging & tooling decisions

- **Package name / import:** distribution `wheeled-biped-rl`, import `wheeled_biped_rl`.
- **Python:** target 3.10+ (matches typical ROS 2 Humble/Jazzy era tooling). Note: the
  current dev machine has 3.9.2 — installing 3.10+ is a quickstart prerequisite.
- **RL framework:** **Tianshou** (chosen over PufferLib: needs PPO *and* SAC,
  modular/testable, asymmetric critic; PufferLib stays a documented throughput
  escape-hatch if the sim is later rewritten in C/GPU and stays PPO-only).
- **Core deps:** `tianshou`, `gymnasium`, `torch`, `numpy`, `pyyaml`. ROS 2 deps are
  **not** pip dependencies — they come from the system ROS 2 install, so Phase 1–3
  stay installable on any machine (incl. the Pi for inference-only).
- **Dependency layering (two-layer + Pi pin):** keep *declaration* and *locking*
  separate — `requirements.txt` is a generated artifact here, not the source of truth.
  - **`pyproject.toml` = abstract deps** (source of truth): loose constraints
    (`torch>=2.2`, `tianshou`, …) + extras; describes what the *package* needs.
  - **Generated lock = pinned**: for reproducible runs, generate a fully pinned lock
    from `pyproject.toml` (`uv.lock`, or `pip compile pyproject.toml -o requirements.txt`).
    Never hand-write it — it is derived. Worth it because RL results drift across
    `torch`/`numpy` versions.
  - **`requirements-pi.txt` = deployment pin**: a *separate* pinned set for the
    Raspberry Pi (CPU/ARM `torch` wheel, often a custom index URL), inference-only and
    distinct from the training-box lock.
  - Rule: declare abstract in `pyproject.toml`; commit a generated lock for
    repeatability; keep the Pi pin separate. (Adopting `uv` — see §8 Q1 — yields the
    lock for free.)
- **Optional extras:** `[ros2]`, `[export]` (onnx), `[dev]` (pytest, ruff, import-linter).
- **Lint/format/test:** ruff + pytest configured in `pyproject.toml`.
- **Scripts:** files in `scripts/` stay thin — argument parsing + a call into
  `wheeled_biped_rl.*`. No real logic in `scripts/` (keeps it testable and reusable).

---

## 8. Open questions to confirm before/while building

These affect structure and are worth pinning down early:

1. **Package manager / env:** plain `pip + venv`, `uv`, or `conda`? (Affects
   `pyproject.toml` and the README quickstart only.) — *still open.*
2. ~~**Action space for v1**~~ — *resolved:* per-side **hip + wheel** command (4-D). Open
   sub-question: velocity/position-target vs torque mode (thesis uses wheel torque + hip PD-position).
3. ~~**Planar vs 3D sim**~~ — *refined:* planar is fine for pitch balance + height + jumps, but
   **yaw/roll needs the lateral/two-track DOF** (thesis: single-side planar can't stabilize yaw).
   Size `RobotState` accordingly.
4. **ROS 2 distro** (Humble vs Jazzy) — pins the `ros2_ws` package format and Python
   version ceiling. Only needed at Phase 4. — *still open.*

---

## 9. Summary

The structure is four stacked layers — **simulation → backends → envs → training** —
with `safety`, `real_world_effects`, `policies`, `deployment`, `ros2`, and `utils`
as cross-cutting siblings, plus a YAML `configs/` tree and a thin `scripts/` CLI
surface. The hard rules are: RL never imports ROS 2, dependencies flow one way, and
the obs/action/safety components are shared between training and deployment. Build it
in phases (Section 6) rather than scaffolding the whole tree up front, so each phase
produces something runnable.
