# Plan - Foundational RL Layer

> Companion to `docs/goal/wheeled_biped_rl_architecture.md`.
> This plan defines the first training layer: a custom Gymnasium environment with a
> reduced-order linkage model. Its job is to make the RL problem coherent before any
> expensive simulator is introduced.

---

## 1. Goal

Build the smallest credible training environment for the wheeled-biped robot.

The foundational layer should answer:

```text
Can a policy learn the task at all?
Are the observation, action, reward, reset, and termination definitions sensible?
Which reward terms and policy interfaces are worth carrying into higher-fidelity training?
```

It should not answer:

```text
Does the detailed mechanism survive every real contact case?
Does the policy transfer directly to hardware?
Which high-fidelity simulator should be final?
```

---

## 2. Scope

Before writing detailed tickets for action space, observation space, rewards, or
training loops, implement the model-candidate repository and interface-versioning
foundation described in:

- `model_candidate_versioning_plan.md`
- `candidate_repository_implementation_plan.md`
- `interface_versioning_plan.md`
- `reward_hyperparameter_repository_plan.md`

Implement:

- `WheeledBipedEnv`, a Gymnasium-compatible environment.
- `PythonSimBackend`, a fast reduced-order backend.
- `RobotState` and `RobotAction` dataclasses.
- `leg_kinematics`, including forward and inverse mappings for the constrained leg.
- `ObservationBuilder`, `ActionAdapter`, `RewardBuilder`, and `TerminationChecker`.
- Tianshou PPO training and evaluation entry points.
- Deterministic tests for API contracts, kinematics, reward signs, action limits, and
  termination behavior.

Do not implement:

- Isaac, MuJoCo, Brax/MJX, or Gazebo training backends.
- ROS 2 inside the RL inner loop.
- full contact-rich 3D simulation.
- hardware deployment.

---

## 3. Model Boundary

The foundational simulator is allowed to be simplified, but it must not encode the
wrong robot.

Rules:

- The policy action is per-side hip plus wheel command: 4-D total.
- The knee is not an independently actuated action.
- The constrained leg linkage is represented by reduced-order kinematics/dynamics.
- The v1 baseline uses a rigid no-spring leg.
- Optional spring and lift-off/contact modes are config-gated later additions.
- Actor observations use only measurable or realistically estimable state.
- Privileged state may exist for diagnostics or an asymmetric critic, but not for the
  deployed actor.

---

## 4. Deliverables

Minimum deliverable:

```text
pip install -e .
pytest
python -m wheeled_biped_rl.training.train_ppo --config ...
python -m wheeled_biped_rl.training.evaluate_policy --checkpoint ...
```

Training success criterion:

```text
PPO can keep the reduced-order robot upright for a full episode while respecting
action, velocity, and posture limits.
```

Follow-on criterion:

```text
The same environment can train velocity tracking under randomized forward-velocity
commands.
```

---

## 5. Tests

Follow the repository TDD rule from `AGENTS.md`.

Core tests:

- `test_env_api`: Gymnasium reset/step shapes, spaces, termination/truncation contract.
- `test_leg_kinematics`: forward/inverse consistency and boundary angles.
- `test_action_adapter`: clipping, scaling, rate limits, and no knee command.
- `test_observation_builder`: actor vs privileged observation separation.
- `test_reward_builder`: balance, pitch, velocity, energy, and smoothness terms.
- `test_termination`: fall, timeout, invalid state, and safety-limit cases.

Training success itself is not a unit test. Use deterministic smoke training only to
catch crashes.

---

## 6. Exit Criteria

The foundational layer is ready to feed the robusting layer when:

- PPO trains without crashes across multiple seeds.
- reward component logs show interpretable behavior.
- the policy-facing observation/action contract is stable.
- the reduced-order linkage model is documented enough to reproduce in candidate
  physics backends.
- checkpoints can be evaluated deterministically.

---

## NET

The foundational layer is the problem-formulation layer: custom Gymnasium, reduced DOF,
fast iteration, Tianshou-compatible, ROS-free. It exists to discover the correct
training interface before spending effort on MuJoCo, Brax/MJX, Isaac, or Gazebo.
