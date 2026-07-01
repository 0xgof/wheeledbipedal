# Plan - Reward and Hyperparameter Repository

> Companion to `model_candidate_versioning_plan.md`.
> This plan defines the repository of reward functions, reward weights, algorithm
> settings, and search spaces used to produce model candidates.

---

## 1. Goal

Make reward and hyperparameter changes explicit, versioned, and queryable.

The project should never have a checkpoint whose reward function or hyperparameters are
known only from memory or terminal history.

---

## 2. Reward Repository

Recommended layout:

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

Reward implementation owns:

- component names;
- component formulas;
- required state/action fields;
- invalid-state handling;
- scalar aggregation contract.

Reward config owns:

- weights;
- thresholds;
- clipping;
- normalization constants;
- enabled/disabled components.

---

## 3. Reward IDs

Reward ids must be stable:

```text
balance_v1
velocity_tracking_v1
balance_energy_penalty_v2
```

Bump reward id when:

- a component formula changes;
- component signs change;
- new required state/action fields are added;
- scalar aggregation changes;
- reward scale changes enough to affect training interpretation.

Do not bump reward id for a pure implementation bug fix, but the candidate manifest still
records the git revision.

---

## 4. Reward Specs

Every candidate snapshots a `reward_spec.yaml`.

Minimum fields:

```yaml
reward_id: balance_v1
implementation: wheeled_biped_rl.rewards.balance_v1
components:
  upright:
    weight: 1.0
  pitch_rate:
    weight: -0.05
  action_magnitude:
    weight: -0.001
scalar_output: weighted_sum
```

Training and evaluation logs must record component values separately.

---

## 5. Hyperparameter Repository

Recommended layout:

```text
configs/algo/
  ppo_foundation_v1.yaml
  ppo_robusting_v1.yaml
  sac_experimental_v1.yaml

configs/search/
  ppo_foundation_grid_v1.yaml
  ppo_foundation_random_v1.yaml
  robusting_backend_bakeoff_v1.yaml
```

Algorithm config owns:

- algorithm name;
- policy network architecture;
- learning rate;
- rollout length;
- batch size;
- discount;
- GAE/lambda when applicable;
- entropy/value/loss coefficients;
- gradient clipping;
- normalization settings;
- seed policy.

Search config owns:

- search method;
- parameter ranges;
- number of trials;
- resource budget;
- promotion metric;
- early-stop rules.

---

## 6. Hyperparameter IDs

Examples:

```text
ppo_foundation_v1
ppo_foundation_grid_v1
ppo_robusting_mujoco_v1
```

Bump ids when changes affect comparability:

- network size;
- optimizer settings;
- rollout length;
- normalization;
- train/eval frequency;
- batch size;
- discount or advantage calculation;
- scheduler/search space.

---

## 7. Candidate Integration

Every candidate stores:

```text
reward_id
reward_spec.yaml
algo_id
hyperparameters.yaml
search_id optional
```

The candidate query CLI should support:

```text
list candidates by reward_id
list candidates by algo_id
compare reward specs
compare hyperparameters
leaderboard grouped by reward_id or algo_id
```

---

## 8. Tests

Core tests:

- reward registry resolves known reward ids;
- unknown reward id fails loudly;
- reward component names are stable;
- reward spec snapshot is written to candidate folder;
- hyperparameter config snapshot is written to candidate folder;
- candidate comparison reports reward/algo mismatches.

Reward behavior tests still live with the reward implementation tickets. This plan only
defines repository and versioning behavior.

---

## NET

Rewards and hyperparameters are first-class versioned inputs to model candidates. Before
building many action/observation/reward tickets, create the structure that names,
snapshots, queries, and compares them.
