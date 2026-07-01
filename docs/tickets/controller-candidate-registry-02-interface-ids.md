# CCR-2 - Required Controller Interface IDs

- Status: `TODO`
- Stage: controller candidate registry / interface versioning
- Depends on: `CCR-1`
- Related: `FL-1`, `FL-2`
- Source plan: `docs/plans/interface_versioning_plan.md`
- Goal: require stable action, observation, task, reward, backend, robot, and mechanism ids in every controller candidate.

## Problem

Candidates are not comparable unless their policy-facing and simulator-facing
interfaces are known. The registry must reject candidates that omit the ids that define
controller meaning.

## Scope

1. Extend `CandidateManifest` or `CandidateRecipe` to require:
   - `action_interface_id`
   - `observation_interface_id`
   - `task_id`
   - `reward_id`
   - `backend_id`
   - `robot_config_id`
   - `mechanism_id`
2. Add validation for lowercase snake-case ids with version suffixes such as `_v1`.
3. Add compatibility helpers that report mismatched ids between two candidates.
4. Add snapshot paths for interface specs where available.
5. Document initial ids:
   - `hip_wheel_4d_v1`
   - `actor_obs_balance_v1`
   - `stand_balance_v1`
   - `balance_v1`
   - `python_sim_v1`
   - `mechanism_rigid_no_spring_v1`

## Non-goals

- implementing action adapter logic.
- implementing observation builder logic.
- implementing reward functions.
- full candidate comparison CLI.

## Files

- `src/wheeled_biped_rl/registry/manifest.py`
- `src/wheeled_biped_rl/registry/query.py` or `lineage.py` if needed
- `configs/interfaces/*.yaml` if creating initial interface specs now
- `tests/test_candidate_interface_ids.py`

## Acceptance

- Candidate creation fails when required interface ids are missing.
- Candidate creation fails when ids are malformed.
- Two candidates with different interface ids are reported as incompatible.
- Valid initial ids pass validation.

## Validation

- TDD required.
- Initial test run must fail before implementation.
- Final validation:
  - `pytest tests/test_candidate_interface_ids.py tests/test_candidate_store.py`
  - `python -m compileall -q src tests`
- Final summary must include initial failing and final passing results.
