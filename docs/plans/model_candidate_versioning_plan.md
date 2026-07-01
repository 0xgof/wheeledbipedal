# Plan - Model Candidate Versioning

> Companion to `foundational_layer_plan.md`, `robusting_layer_plan.md`, and
> `gazebo_validation_feedback_plan.md`.
> This plan defines how trained policy candidates, reward definitions, hyperparameters,
> configs, checkpoints, metrics, validation results, and lineage are stored and queried.

---

## 1. Goal

Create a repository of model candidates that makes training work reproducible and
searchable.

The system should answer:

```text
Which reward function produced this checkpoint?
Which hyperparameters and config snapshot were used?
Which simulator/backend trained it?
Which validation scenarios did it pass or fail?
Which candidate is the current best for balance, velocity tracking, or deployment?
Can this run be resumed or reproduced?
```

This is model candidate versioning, not a model registry for production serving.

Detailed implementation plans:

- `controller_candidate_registry_plan.md`
- `candidate_repository_implementation_plan.md`
- `interface_versioning_plan.md`
- `reward_hyperparameter_repository_plan.md`
- `robot_mechanism_versioning_plan.md`
- `backend_randomization_curriculum_plan.md`
- `validation_evaluation_registry_plan.md`
- `deployment_runtime_assumptions_plan.md`
- `artifact_retention_reproducibility_plan.md`

---

## 2. Core Concepts

### Candidate

A candidate is one trained policy artifact plus its metadata.

Required identity:

```text
candidate_id
run_id
checkpoint_id
parent_candidate_id optional
created_at
git_revision
training_layer
backend
task
```

### Recipe

A recipe is the immutable input definition that produced candidates.

It includes:

- reward function name and version;
- reward weights;
- observation/action interface version;
- algorithm and hyperparameters;
- environment/task config;
- robot config version;
- domain-randomization profile;
- backend config;
- seed policy.

### Evaluation

An evaluation is a deterministic or repeated measurement of a candidate.

Examples:

- foundational env evaluation;
- robusting backend evaluation;
- Gazebo checkpoint gate;
- deployment benchmark;
- manual hardware trial later.

---

## 3. Storage Layout

Use append-only run artifacts plus queryable indexes.

Recommended local layout:

```text
runs/
  candidates/
    <candidate_id>/
      candidate.yaml
      recipe.yaml
      resolved_config.yaml
      reward_spec.yaml
      hyperparameters.yaml
      metrics.jsonl
      evaluations.jsonl
      lineage.yaml
      checkpoints/
        checkpoint_000100.pt
        checkpoint_000200.pt
      exports/
        policy.onnx
        policy.torchscript
      artifacts/
        plots/
        videos/
        gazebo_logs/

  indexes/
    candidates.jsonl
    evaluations.jsonl
    leaderboard_balance.csv
    leaderboard_velocity.csv
```

`candidate.yaml` is the manifest. It should be small and human-readable.

`metrics.jsonl` and `evaluations.jsonl` are append-only so long runs and remote jobs can
write incrementally.

---

## 4. Reward Function Repository

Reward functions need explicit versions.

Recommended code/config split:

```text
src/wheeled_biped_rl/rewards/
  __init__.py
  registry.py
  balance_v1.py
  velocity_tracking_v1.py

configs/rewards/
  balance_v1.yaml
  velocity_tracking_v1.yaml
```

Rules:

- reward implementation has a stable `reward_id`, e.g. `balance_v1`;
- reward config records weights and thresholds;
- changing reward behavior creates a new reward version unless it is a bug fix;
- bug fixes must record `reward_code_revision` through the git commit;
- reward components are logged separately for every training and evaluation run.

Do not identify rewards only by free-text notes.

---

## 5. Hyperparameter Repository

Hyperparameters should be named and versioned.

Recommended config layout:

```text
configs/algo/
  ppo_foundation_v1.yaml
  ppo_robusting_v1.yaml
  sac_experimental_v1.yaml

configs/search/
  ppo_foundation_grid_v1.yaml
  ppo_robusting_sweep_v1.yaml
```

Rules:

- every run stores the fully resolved hyperparameter snapshot;
- sweep definitions are versioned separately from the resulting candidates;
- candidate manifests record whether the run was single-run, grid, random search, or
  scheduler-generated;
- changes to optimizer, network, rollout length, reward scale, or normalization are
  candidate-relevant and must be captured.

---

## 6. Candidate Manifest

Minimum `candidate.yaml`:

```yaml
candidate_id: cand_20260701_120000_ab12
run_id: run_20260701_115500_ppo_balance
checkpoint_id: checkpoint_000200
parent_candidate_id: null
created_at: "2026-07-01T12:00:00Z"

git_revision: "<commit>"
training_layer: foundational
backend:
  name: python_sim
  version: "v1"
  device: cpu

task_id: stand_balance_v1
reward_id: balance_v1
algo_id: ppo_foundation_v1
observation_interface_id: actor_obs_v1
action_interface_id: hip_wheel_4d_v1

artifacts:
  checkpoint: checkpoints/checkpoint_000200.pt
  resolved_config: resolved_config.yaml
  reward_spec: reward_spec.yaml
  hyperparameters: hyperparameters.yaml
  metrics: metrics.jsonl
  evaluations: evaluations.jsonl

status: candidate
tags:
  - balance
  - foundation
```

Statuses:

```text
candidate
promoted
rejected
archived
deployment_candidate
hardware_tested
```

---

## 7. Query Interface

Start simple: file-backed indexes and a small CLI.

Example commands:

```text
python -m wheeled_biped_rl.registry.index_runs runs/candidates
python -m wheeled_biped_rl.registry.list_candidates --task stand_balance_v1
python -m wheeled_biped_rl.registry.show cand_20260701_120000_ab12
python -m wheeled_biped_rl.registry.compare cand_a cand_b
python -m wheeled_biped_rl.registry.leaderboard --scenario balance_nominal
```

Query fields:

- candidate id;
- task;
- reward id;
- algorithm id;
- backend;
- training layer;
- seed;
- parent candidate;
- pass/fail validation status;
- score;
- tags;
- creation time;
- git revision.

If the file-backed registry becomes painful, migrate the index to SQLite. The artifact
layout should remain stable so the storage backend can change without moving files.

---

## 8. Lineage

Every candidate should know its origin.

Lineage examples:

```text
foundation candidate -> robusting fine-tune -> Gazebo-promoted candidate
candidate A -> reward-weight tweak -> candidate B
candidate B -> MuJoCo fine-tune -> candidate C
candidate C -> ONNX export -> deployment candidate
```

Lineage should record:

- parent candidate id;
- reason for fork;
- changed recipe fields;
- training layer transition;
- validation gate that promoted or rejected the candidate.

---

## 9. HPC and Remote Runs

HPC jobs must write the same artifacts as local runs.

Required behavior:

- generate candidate/run id before job submission;
- write resolved config and recipe at job start;
- append metrics during training;
- save checkpoints at configured intervals;
- write final candidate manifest even on failure when possible;
- sync artifacts back to the candidate repository;
- include scheduler metadata such as job id, node type, CPU/GPU request, wall time, and
  exit status.

The registry must tolerate partial runs and failed candidates.

---

## 10. Gazebo Feedback Integration

Gazebo validation writes evaluation records into the same candidate store.

Evaluation record fields:

```text
candidate_id
checkpoint_id
validation_layer
scenario_id
seed
pass
score
metrics
failure_reason
artifact_paths
created_at
```

The robusting layer can query these records for checkpoint gates:

```text
continue if candidate passes required Gazebo scenarios
promote if candidate improves leaderboard score
reject or pause if deterministic validation fails
```

Gazebo feedback must be explicit and config-driven. It should not silently mutate reward
functions or hyperparameters.

---

## 11. Implementation Phases

### Phase 1 - Manifest and Local Artifacts

- write candidate manifests;
- snapshot resolved config, reward spec, and hyperparameters;
- append metrics/evaluations as JSONL;
- add local query CLI over files.

### Phase 2 - Reward and Hyperparameter Registries

- add reward registry with stable reward ids;
- add named algorithm/hyperparameter configs;
- log reward components consistently.

### Phase 3 - Lineage and Promotion

- add parent candidate tracking;
- add status transitions;
- add compare and leaderboard commands.

### Phase 4 - HPC Support

- add remote job metadata;
- support artifact sync;
- tolerate partial/failed runs.

### Phase 5 - Gazebo Feedback

- ingest Gazebo validation records;
- implement checkpoint gate queries;
- add promotion/rejection rules.

---

## 12. Non-Goals

- serving models in production.
- replacing experiment tracking tools with a full web UI.
- storing large binary artifacts in Git.
- making a database mandatory before file-backed indexes are insufficient.
- allowing unversioned reward functions or ad hoc hyperparameters to define a candidate.

---

## NET

Model candidate versioning is the project memory for training. Every candidate must have
a manifest, recipe, config snapshot, reward version, hyperparameters, metrics,
evaluations, artifacts, and lineage. Start file-backed and queryable; migrate the index
to SQLite only when needed. Gazebo feedback and HPC runs write into the same candidate
store.
