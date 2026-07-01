# Plan - Candidate Repository Implementation

> Companion to `model_candidate_versioning_plan.md`.
> This plan turns the model-candidate concept into concrete files, modules, commands,
> and implementation phases. Build this before writing detailed action-space,
> observation-space, reward, or training-loop tickets.

---

## 1. Goal

Create the project-local artifact repository used by every training layer.

The first implementation should be simple:

```text
file-backed manifests
append-only JSONL metrics/evaluations
small query CLI
no mandatory database
```

The repository must make every checkpoint traceable to:

- code revision;
- robot config;
- backend;
- task;
- action/observation interface versions;
- reward function and reward weights;
- algorithm hyperparameters;
- training seed;
- evaluation and validation results.

---

## 2. Package Structure

Recommended modules:

```text
src/wheeled_biped_rl/
  registry/
    __init__.py
    ids.py
    manifest.py
    store.py
    index.py
    query.py
    lineage.py
    cli.py
```

Responsibilities:

| Module | Owns |
|---|---|
| `ids.py` | candidate/run/checkpoint id generation and validation |
| `manifest.py` | dataclasses or pydantic models for manifests and evaluations |
| `store.py` | filesystem layout, read/write, atomic-ish manifest writes |
| `index.py` | rebuild query indexes from candidate folders |
| `query.py` | filters, comparisons, leaderboard logic |
| `lineage.py` | parent/child candidate relationships |
| `cli.py` | command-line entry points |

Keep the registry independent from Tianshou, Gymnasium, ROS 2, and simulator backends.

---

## 3. Artifact Layout

Canonical local layout:

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
      exports/
      artifacts/
  indexes/
    candidates.jsonl
    evaluations.jsonl
```

Rules:

- `candidate.yaml` is required.
- `recipe.yaml` is required for any training-produced candidate.
- `resolved_config.yaml` is required for reproducibility.
- `metrics.jsonl` and `evaluations.jsonl` are append-only.
- checkpoints and exports are referenced by relative path from `candidate.yaml`.
- failed/partial runs should still write a manifest when possible.

---

## 4. CLI

Minimum commands:

```text
python -m wheeled_biped_rl.registry.cli init --root runs
python -m wheeled_biped_rl.registry.cli create-candidate --recipe recipe.yaml
python -m wheeled_biped_rl.registry.cli index --root runs
python -m wheeled_biped_rl.registry.cli list --task stand_balance_v1
python -m wheeled_biped_rl.registry.cli show <candidate_id>
python -m wheeled_biped_rl.registry.cli compare <candidate_a> <candidate_b>
python -m wheeled_biped_rl.registry.cli leaderboard --scenario balance_nominal
```

Training code may call the same registry functions directly instead of shelling out.

---

## 5. Data Models

Start with typed Python models. Pydantic is acceptable if `CFG-2` has already introduced
it; otherwise dataclasses plus explicit validation are fine for the first pass.

Core models:

```text
CandidateManifest
CandidateRecipe
ArtifactRefs
MetricRecord
EvaluationRecord
LineageRecord
```

Validation rules:

- ids match expected prefixes;
- referenced artifact paths are relative;
- required recipe/interface/reward/hyperparameter ids exist;
- status is one of the allowed values;
- timestamps are ISO-8601 strings;
- JSONL records are parseable and include candidate/checkpoint ids.

---

## 6. Query Index

The first index is derived, not authoritative.

Build it by scanning `runs/candidates/*/candidate.yaml` and appending normalized rows to:

```text
runs/indexes/candidates.jsonl
runs/indexes/evaluations.jsonl
```

If file-backed indexes become too slow or awkward, migrate indexes to SQLite while
keeping the artifact layout stable.

---

## 7. Integration Points

Foundational layer:

- create a candidate at training start;
- write recipe and resolved config before rollout begins;
- append reward metrics during training;
- save checkpoints under the candidate folder;
- append deterministic evaluation records.

Robusting layer:

- preserve parent candidate id when fine-tuning;
- record backend and HPC metadata;
- write checkpoint-gate results.

Gazebo validation:

- append evaluation records for scenario results;
- attach logs/videos under `artifacts/gazebo_logs/`;
- promote/reject candidates through explicit status changes.

---

## 8. Implementation Phases

### Phase 1 - Local Manifest Store

- create registry package;
- implement id generation;
- write/read candidate manifests;
- write recipe/config snapshots;
- append metrics/evaluations;
- add basic tests.

### Phase 2 - Query CLI

- implement index rebuild;
- list/show/filter candidates;
- compare candidates;
- simple leaderboard by evaluation score.

### Phase 3 - Training Integration

- wire foundational training scripts to create candidates;
- write checkpoints and metrics through the store;
- emit deterministic evaluation records.

### Phase 4 - Lineage and Promotion

- parent candidate support;
- status transitions;
- promotion/rejection reasons;
- validation gate records.

### Phase 5 - Remote/HPC Robustness

- tolerate partial runs;
- scheduler metadata;
- artifact sync/import;
- failed-run manifests.

---

## 9. Tests

Core tests:

- id generation is deterministic in shape and collision-resistant enough for local use;
- manifest validation rejects missing required fields;
- store writes and reads candidate folders;
- JSONL append preserves existing records;
- index rebuild discovers candidates;
- query filters by task, backend, reward id, and status;
- lineage can trace parent candidates.

No test should require a simulator, ROS 2, Tianshou, or GPU.

---

## NET

Build the candidate repository as a small file-backed registry first. It is the
accounting layer for every later action, observation, reward, training, robusting, and
Gazebo validation decision.
