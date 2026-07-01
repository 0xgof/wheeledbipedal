# Plan - Controller Candidate Registry

> Supersedes the narrower "model candidate" framing. A model checkpoint is only one
> artifact inside a controller candidate.

---

## 1. Goal

Version complete controller candidates, not just neural-network weights.

A controller candidate is:

```text
policy/checkpoint/export
+ robot and mechanism assumptions
+ action and observation contracts
+ reward and training recipe
+ simulator/backend assumptions
+ randomization and curriculum
+ validation/evaluation results
+ deployment/runtime assumptions
```

The registry should answer:

```text
What exactly was trained?
Why is this checkpoint compatible or incompatible with another?
Which assumptions did it rely on?
Which validations did it pass?
Can it be resumed, reproduced, promoted, or rejected?
```

---

## 2. Candidate Object

Minimum top-level identity:

```text
controller_candidate_id
run_id
checkpoint_id
parent_candidate_id optional
created_at
git_revision
dirty_tree flag
status
```

The candidate manifest references versioned sub-records:

- robot configuration;
- mechanism model;
- action interface;
- observation interface;
- reward function and weights;
- algorithm/hyperparameters;
- backend/simulator;
- domain randomization;
- curriculum;
- validation scenarios;
- evaluation records;
- deployment/runtime profile;
- artifacts.

---

## 3. Storage

Use the same artifact layout proposed in `model_candidate_versioning_plan.md`, but name
the concept as a controller candidate:

```text
runs/
  candidates/
    <controller_candidate_id>/
      candidate.yaml
      recipe.yaml
      resolved_config.yaml
      artifacts/
      checkpoints/
      exports/
      metrics.jsonl
      evaluations.jsonl
```

The model checkpoint lives under `checkpoints/`; it is not the candidate itself.

---

## 4. Promotion

Allowed statuses:

```text
candidate
promoted
rejected
archived
deployment_candidate
hardware_tested
```

Promotion should be explicit and recorded with:

- criterion;
- evaluator;
- validation scenario ids;
- metric threshold;
- failure/promotion reason;
- timestamp.

---

## 5. Relationship to Existing Plans

This plan coordinates:

- `candidate_repository_implementation_plan.md`
- `interface_versioning_plan.md`
- `reward_hyperparameter_repository_plan.md`
- `robot_mechanism_versioning_plan.md`
- `backend_randomization_curriculum_plan.md`
- `validation_evaluation_registry_plan.md`
- `deployment_runtime_assumptions_plan.md`
- `artifact_retention_reproducibility_plan.md`

---

## NET

The registry stores controller candidates. A model checkpoint is just one artifact.
Every assumption that changes controller meaning must be named, snapshotted, and
queryable.
