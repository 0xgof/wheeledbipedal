# CCR-3 - Reward and Hyperparameter Snapshots

- Status: `TODO`
- Stage: controller candidate registry / recipe snapshots
- Depends on: `CCR-1`, `CCR-2`
- Related: future reward and training tickets
- Source plan: `docs/plans/reward_hyperparameter_repository_plan.md`
- Goal: store reward specs and hyperparameter snapshots for every controller candidate before reward/training implementation begins.

## Problem

Reward and hyperparameter changes alter controller meaning. The registry must support
snapshotting these inputs before detailed reward functions and training scripts are
implemented.

## Scope

1. Add artifact references for:
   - `reward_spec.yaml`
   - `hyperparameters.yaml`
2. Add store methods to write/read these snapshots.
3. Require `reward_id` and `algo_id` in candidate recipes.
4. Add minimal placeholder reward and hyperparameter config examples if needed.
5. Ensure snapshots are copied into the candidate folder, not referenced only by mutable
   source paths.

## Non-goals

- reward formula implementation.
- PPO/Tianshou implementation.
- hyperparameter search.
- W&B/MLflow/SageMaker integration.

## Files

- `src/wheeled_biped_rl/registry/manifest.py`
- `src/wheeled_biped_rl/registry/store.py`
- `configs/rewards/balance_v1.yaml` if needed
- `configs/algo/ppo_foundation_v1.yaml` if needed
- `tests/test_candidate_recipe_snapshots.py`

## Acceptance

- Candidate folders can include immutable reward and hyperparameter snapshots.
- Store rejects recipes missing `reward_id` or `algo_id`.
- Snapshot files round-trip through the store.
- Candidate manifest points to the candidate-local snapshots.

## Validation

- TDD required.
- Initial test run must fail before implementation.
- Final validation:
  - `pytest tests/test_candidate_recipe_snapshots.py tests/test_candidate_store.py`
  - `python -m compileall -q src tests`
- Final summary must include initial failing and final passing results.
