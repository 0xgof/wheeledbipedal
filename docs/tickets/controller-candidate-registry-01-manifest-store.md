# CCR-1 - Controller Candidate Manifest Store

- Status: `TODO`
- Stage: controller candidate registry / local artifact store
- Depends on: `PB-1`
- Related: `CCR-2`, `CCR-3`, `CCR-4`
- Source plan: `docs/plans/candidate_repository_implementation_plan.md`
- Goal: implement the minimal file-backed store for controller candidate manifests and append-only records.

## Problem

Before training starts, the repository needs a durable place to record what a controller
candidate is. Checkpoints alone are insufficient; every candidate needs a manifest,
recipe snapshot, config snapshot, metrics stream, and evaluation stream.

## Scope

1. Implement candidate/run/checkpoint id helpers.
2. Implement a `CandidateManifest` data model.
3. Implement a local store that creates:
   ```text
   runs/candidates/<candidate_id>/
     candidate.yaml
     recipe.yaml
     resolved_config.yaml
     metrics.jsonl
     evaluations.jsonl
     checkpoints/
     exports/
     artifacts/
   ```
4. Implement read/write for `candidate.yaml`.
5. Implement append for `metrics.jsonl` and `evaluations.jsonl`.
6. Use relative artifact paths inside manifests.
7. Keep the registry independent from Gymnasium, Tianshou, ROS 2, and simulator backends.

## Non-goals

- query CLI.
- lineage graph.
- reward or hyperparameter registry.
- training integration.
- database or cloud backend.

## Files

- `src/wheeled_biped_rl/registry/ids.py`
- `src/wheeled_biped_rl/registry/manifest.py`
- `src/wheeled_biped_rl/registry/store.py`
- `tests/test_registry_ids.py`
- `tests/test_candidate_store.py`

## Acceptance

- A candidate folder can be created from a manifest.
- Manifest read/write round-trips without losing required fields.
- Metrics and evaluations append as JSONL without overwriting existing records.
- Invalid ids or missing required manifest fields fail clearly.
- Store tests use temporary directories and do not write to the real `runs/` folder.

## Validation

- TDD required.
- Initial test run must fail before implementation for missing registry behavior.
- Final validation:
  - `pytest tests/test_registry_ids.py tests/test_candidate_store.py`
  - `python -m compileall -q src tests`
- Final summary must include initial failing and final passing results.
