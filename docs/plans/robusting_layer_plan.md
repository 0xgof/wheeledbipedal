# Plan - Robusting Training Layer

> Companion to `foundational_layer_plan.md` and
> `gazebo_validation_feedback_plan.md`.
> This plan defines the second training layer: one or more stronger physics backends
> used after the custom Gymnasium environment proves the RL formulation.

---

## 1. Goal

Use a more capable simulator to make policies robust.

This layer should improve:

- contact and friction modelling;
- actuator limits and dynamics;
- mass, inertia, and center-of-mass variation;
- sensor and action delay;
- domain randomization;
- larger-scale training or fine-tuning;
- repeatable benchmark and checkpoint evaluation.

The layer must preserve the policy-facing contract learned in the foundational layer:

```text
observation -> policy -> action -> env.step(action)
```

---

## 2. Candidate Backends

Candidate technologies:

- MuJoCo / MJCF.
- Brax / MJX.
- Isaac Lab / Isaac Sim.
- another backend only if it beats the above on evidence.

Gazebo/SDF may participate in feasibility tests, but its default role is validation and
integration, not primary training.

Do not assume NVIDIA GPU access. Keep a CPU-friendly path viable through the reduced
Python environment and/or MuJoCo. Treat Isaac and GPU-oriented JAX paths as options
that must be proven against actual hardware availability.

---

## 3. Backend Abstraction

The robusting layer should support multiple technologies through a common training
adapter.

Conceptual interface:

```python
class TrainingBackend:
    def reset(self, seed: int | None = None) -> BackendState:
        ...

    def step(self, action_batch: ActionBatch) -> StepBatch:
        ...

    def close(self) -> None:
        ...
```

The adapter must expose:

- actor observation batch;
- optional privileged critic observation batch;
- action application;
- reward component metrics;
- termination/truncation flags;
- reset reasons;
- deterministic evaluation mode;
- backend metadata: simulator, version, device, seed, config snapshot.

Backend-specific code lives behind this adapter. Training code should not branch on
MuJoCo vs Brax vs Isaac except at construction/configuration time.

---

## 4. Feasibility Bakeoff

Before selecting the serious backend, build the same minimal linkage in each candidate.

Evaluate:

- whether the constrained leg can be represented without training the wrong mechanism;
- constraint stability under hip and wheel actuation;
- contact/friction behavior at the wheel;
- actuator limits and command modes;
- reset reliability;
- deterministic replay;
- step throughput;
- parallel environment count;
- CPU/GPU requirements;
- HPC deployment friction;
- checkpoint export/import compatibility.

Minimum bakeoff artifact per backend:

```text
backend smoke script
minimal linkage model
fixed action rollout
deterministic reset/eval script
throughput report
failure notes
```

---

## 5. HPC Requirements

The robusting layer must be runnable outside the local workstation.

Required HPC properties:

- non-interactive CLI entry points;
- config-driven runs;
- no GUI requirement;
- deterministic seeds;
- resumable checkpoints;
- run directory with config snapshot, dependency lock, git revision, and backend metadata;
- separate train and evaluation commands;
- clear CPU/GPU resource request examples;
- logs in portable formats such as CSV, JSONL, TensorBoard, or WandB offline files.
- model candidate artifacts compatible with
  `docs/plans/model_candidate_versioning_plan.md`.

Expected job modes:

```text
single-seed training
multi-seed sweep
backend bakeoff benchmark
checkpoint evaluation
Gazebo-gated checkpoint validation, when available
```

Do not make the robusting layer depend on a local desktop, RViz, or ROS GUI.

---

## 6. Gazebo Feedback Hook

The robusting layer should have an optional checkpoint gate that can call the Gazebo
validation layer before continuing a long training run.

Conceptual flow:

```text
train for N iterations
save checkpoint
run deterministic local evaluation
if local eval passes:
    submit or run Gazebo validation
if Gazebo validation passes:
    continue training / promote checkpoint
else:
    lower checkpoint score, adjust curriculum, or stop/pause according to config
```

The hook should be optional because Gazebo validation will be slower than the training
simulator and may require a ROS-enabled environment.

The hook must not put ROS 2 inside the main PPO/SAC collection loop.

---

## 7. Exit Criteria

The robusting layer is useful when:

- at least one serious backend can run the minimal linkage reliably;
- training can run headlessly on local machine and HPC;
- checkpoints are deterministic enough to compare;
- policies trained here can be exported to the validation layer;
- Gazebo feedback can be enabled without rewriting the trainer.

---

## NET

The robusting layer is an evidence-driven training layer. It should let the project
choose MuJoCo, Brax/MJX, Isaac, or another backend without rewriting the policy-facing
interface. It must support HPC, checkpointing, deterministic evaluation, and optional
Gazebo feedback.
