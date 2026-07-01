# CCR-4 - Local Candidate Query CLI

- Status: `TODO`
- Stage: controller candidate registry / local query
- Depends on: `CCR-1`, `CCR-2`, `CCR-3`
- Related: robusting and validation layers
- Source plan: `docs/plans/candidate_repository_implementation_plan.md`
- Goal: provide a small CLI to inspect local controller candidates before training produces many runs.

## Problem

Once candidates exist, users need to list, inspect, and compare them without manually
opening manifest files. The first query layer should remain file-backed and simple.

## Scope

1. Implement index rebuilding by scanning `runs/candidates/*/candidate.yaml`.
2. Write derived indexes:
   - `runs/indexes/candidates.jsonl`
   - `runs/indexes/evaluations.jsonl`
3. Implement CLI commands:
   - `index`
   - `list`
   - `show`
   - `compare`
4. Support filters for:
   - task id;
   - reward id;
   - backend id;
   - status;
   - parent candidate id.
5. Compare command should report interface/reward/backend mismatches clearly.

## Non-goals

- SQLite.
- cloud tracking integration.
- web UI.
- training integration.
- leaderboard scoring beyond simple evaluation record sorting.

## Files

- `src/wheeled_biped_rl/registry/index.py`
- `src/wheeled_biped_rl/registry/query.py`
- `src/wheeled_biped_rl/registry/cli.py`
- `tests/test_candidate_index.py`
- `tests/test_candidate_query_cli.py`

## Acceptance

- Index rebuild discovers candidates in a temporary `runs/` tree.
- `list` filters by task/reward/backend/status.
- `show` prints or returns one candidate manifest.
- `compare` reports compatible candidates and specific mismatches.
- CLI tests do not require real training artifacts.

## Validation

- TDD required.
- Initial test run must fail before implementation.
- Final validation:
  - `pytest tests/test_candidate_index.py tests/test_candidate_query_cli.py`
  - `python -m compileall -q src tests`
- Final summary must include initial failing and final passing results.
