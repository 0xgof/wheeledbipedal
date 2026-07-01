# PB-1 - Python Package Bootstrap

- Status: `TODO`
- Stage: Python package bootstrap / Phase 0
- Depends on: none
- Related: `CCR-1`, `FL-1`
- Source plan: `docs/plans/repo_structure_plan.md`
- Goal: create the minimal importable Python package and test harness used by all RL and registry work.

## Problem

The repository currently has ROS 2 description code and plans, but no importable
`wheeled_biped_rl` Python package. The controller-candidate registry and foundational
environment need a clean package skeleton before implementation starts.

## Scope

1. Create `pyproject.toml` with package metadata and pytest configuration.
2. Create `src/wheeled_biped_rl/__init__.py`.
3. Create minimal package directories needed immediately:
   - `src/wheeled_biped_rl/registry/`
   - `src/wheeled_biped_rl/utils/`
4. Add `tests/test_import.py`.
5. Add any minimal dev dependency declarations needed for tests.
6. Respect repository style:
   - do not run Black;
   - do not run `ruff format`;
   - keep Python files below 700 lines.

## Non-goals

- registry implementation.
- Gymnasium environment.
- robot dynamics.
- Tianshou training.
- ROS 2 package changes.

## Files

- `pyproject.toml`
- `src/wheeled_biped_rl/__init__.py`
- `src/wheeled_biped_rl/registry/__init__.py`
- `src/wheeled_biped_rl/utils/__init__.py`
- `tests/test_import.py`

## Acceptance

- `wheeled_biped_rl` imports from an editable install.
- `pytest` discovers and runs the import smoke test.
- The package uses `src/` layout.
- No ROS 2 dependency is required for the Python package import.

## Validation

- TDD is not required beyond the import smoke test because this is scaffolding.
- Run:
  - `pip install -e .`
  - `pytest`
  - `python -m compileall -q src tests`
- Final summary must include the commands and results.
