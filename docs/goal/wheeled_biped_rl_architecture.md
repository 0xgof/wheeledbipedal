# Wheeled-Biped Robot RL Training Pipeline: Goal and Architecture Preview

## 1. Purpose of this repository

This repository will implement a reinforcement learning training pipeline for a **wheeled-biped / wheeled-legged balancing robot**.

The target robot is not a conventional walking humanoid. It is a dynamically balancing robot with:

- two articulated legs;
- hip and knee mechanisms;
- actuated wheels at the feet;
- a body-mounted payload containing batteries, compute, and motors;
- a high centre of mass;
- nonlinear leg linkage mechanics;
- a control problem combining balance, posture, wheel locomotion, and leg coordination.

The primary goal is to train policies using **PPO and/or SAC**, initially in simulation, and later prepare them for deployment through a **ROS 2-based robot control stack**.

The intended implementation should be modular enough to support:

1. fast early experimentation in a custom Python simulator;
2. later integration with ROS 2 and a higher-fidelity simulator such as Gazebo, Ignition/Gazebo Sim, Isaac Sim, or another compatible backend;
3. eventual deployment of a trained PyTorch policy as a ROS 2 node controlling the physical robot through a safety and low-level control layer.

The repository should be written with the assumption that **Tianshou** is the preferred reinforcement learning framework.

---

## 2. High-level problem framing

The robot should be treated as a **wheeled-legged inverted-pendulum system**, not as a classic walking biped.

The core behaviours to learn are expected to be incremental:

1. **Balance in place**
   - keep the body upright;
   - prevent falling;
   - maintain a stable body height and pitch.

2. **Velocity tracking**
   - move forward and backward while staying balanced;
   - track commanded linear velocity.

3. **Turning**
   - track angular/yaw commands using differential wheel motion;
   - preserve balance during turning.

4. **Posture and height adaptation**
   - adjust leg configuration;
   - maintain or change body height;
   - eventually support terrain adaptation or obstacle handling.

The first implementation should not attempt the full behaviour immediately. The initial objective should be a minimal, stable PPO training loop for balance and simple velocity tracking.

---

## 3. Behaviour strategy: specialist skills, command-conditioned policies, and hierarchy

The long-term goal is **not only to teach the robot to self-balance**. Balance is the foundational skill, but the repository should support a broader family of behaviours, including:

```text
standing balance
straight-line velocity tracking
curved-path tracking
turning in place
payload compensation
height/posture adaptation
recovery from disturbances
one-wheel balance or other special dynamic modes
```

A weak initial assumption would be:

> one behaviour = one trained model

That can be useful during early experiments, but it should not be the only architecture supported by the repository. Many behaviours are better represented as different **commands** given to the same low-level control policy.

### 3.1 Specialist policies

The repository should support specialist policies because they are useful for debugging and for difficult isolated skills.

Examples:

```text
policy_stand_balance.pt
policy_velocity_tracking.pt
policy_payload_robust_balance.pt
policy_one_wheel_balance.pt
```

Specialist policies are easier to train and evaluate, but they create a deployment problem: the robot then needs a policy-switching mechanism. Abrupt transitions between policies can cause discontinuous actions, which is dangerous for a dynamically balancing robot.

Specialist policies are therefore useful for research, staged development, and hard experimental skills, but they should not automatically become the final deployment architecture.

### 3.2 Command-conditioned generalist policy

The preferred long-term direction should be a **compact command-conditioned generalist policy**.

Instead of training one model for every behaviour, train one policy that receives both robot state and desired command as input.

A command vector may initially contain:

```text
target_forward_velocity
target_yaw_rate
target_body_height
```

Later versions may add:

```text
target_roll_angle
target_pitch_offset
balance_mode_id
payload_estimate
terrain_mode_id
```

This lets a single policy represent several behaviours:

```text
stand still:             target_forward_velocity = 0, target_yaw_rate = 0
move straight:           target_forward_velocity > 0, target_yaw_rate = 0
move along a curve:      target_forward_velocity > 0, target_yaw_rate != 0
turn in place:           target_forward_velocity = 0, target_yaw_rate != 0
change posture/height:   target_body_height changes
```

Payload compensation should usually be handled through **domain randomization** and, if available, an estimated payload input. The policy should be trained across a distribution of payload masses, payload positions, and centre-of-mass offsets instead of training one model per payload.

A useful command-conditioned observation structure is:

```text
observation = robot_state + previous_action + command_vector + optional_estimates
```

This is more scalable than maintaining a growing collection of independent behaviour-specific models.

### 3.3 Hierarchical control

The recommended long-term control architecture is hierarchical:

```text
high-level planner / command generator
        ↓
command-conditioned RL locomotion policy
        ↓
action adapter
        ↓
safety supervisor
        ↓
low-level motor controllers
        ↓
physical robot
```

The high-level planner decides what the robot should do. The low-level RL policy focuses on robustly executing commands while staying balanced.

Examples:

```text
planner command: follow curved path
        ↓
policy command: target_forward_velocity = 0.4 m/s, target_yaw_rate = 0.25 rad/s
```

This keeps the RL policy focused on balance, posture, and local locomotion rather than full navigation or task planning.

### 3.4 Relationship between the generalist policy and hierarchical control

The command-conditioned generalist policy and hierarchical control should not be treated as mutually exclusive alternatives. They are complementary layers of the same long-term control architecture.

The recommended development path is:

```text
Phase 1: train a compact command-conditioned generalist policy
    robot state + command vector -> stable low-level action

Phase 2: add hierarchical control above it
    task/path/mission -> command sequence -> generalist policy -> action

Phase 3: add specialist policies only where justified
    rare, risky, or dynamically distinct behaviours -> specialist model or mode-conditioned extension
```

In this framing, the command-conditioned policy is the learned low-level locomotion and balance controller. The hierarchical layer is a planner, behaviour manager, or command generator that decides what the robot should attempt next.

A typical final architecture should look like:

```text
high-level planner / behaviour manager
        ↓
command-conditioned generalist locomotion policy
        ↓
safety layer / action adapter
        ↓
low-level motor controllers
        ↓
robot hardware
```

The high-level layer can use the same policy for several behaviours by changing the command vector:

```text
straight-line motion:
    target_forward_velocity = 0.5
    target_yaw_rate = 0.0
    target_body_height = normal

curved-path motion:
    target_forward_velocity = 0.4
    target_yaw_rate = 0.3
    target_body_height = normal

payload compensation:
    same motion command
    payload estimate or payload-randomized dynamics change

height/posture change:
    target_forward_velocity = 0.0 or low
    target_body_height = low/high

disturbance recovery:
    command temporarily prioritizes stabilization or reduced velocity
```

This means the repository should first focus on training a reliable command-conditioned policy. Hierarchical control can then be built on top without replacing the generalist policy.

Specialist policies remain valid, but they should be added selectively. Good candidates include:

```text
one-wheel balance
extreme recovery manoeuvres
self-righting after a fall
precise docking or calibration routines
emergency stabilization behaviours
```

Less suitable candidates for separate specialist models are normal behaviours such as straight-line motion, curved paths, moderate turning, normal payload changes, standing still, and height adjustment. These should usually be handled by the command-conditioned generalist policy.

If specialist models are added, the repository should eventually include a **policy manager / behaviour manager** responsible for:

```text
selecting the active policy
checking transition conditions
preventing unsafe policy switches
optionally blending actions during transitions
falling back to a safe stabilization controller
logging active policy and transition events
```

The safety layer should remain active regardless of whether the current action comes from the generalist policy, a specialist model, or a non-RL fallback controller.

### 3.5 One-wheel balance as a special case

One-wheel balance may be dynamically different from normal two-wheel balance because the contact mode changes.

Normal mode:

```text
left wheel contact + right wheel contact
```

One-wheel mode:

```text
single wheel contact
larger roll dynamics
smaller support region
higher instability risk
```

For this reason, one-wheel balance may deserve a specialist policy during early development. Later, it could be integrated into a generalist policy through:

```text
mode-conditioned training
policy distillation
hierarchical policy switching with smooth transitions
```

The repository should therefore support both:

```text
specialist training: one task config → one policy
generalist training: multiple task configs/commands → one policy
```

### 3.6 Task configuration model

The repo should organize behaviours as task/config definitions rather than hard-coded training scripts.

Example:

```text
configs/tasks/
    stand_balance.yaml
    velocity_tracking.yaml
    curved_path_tracking.yaml
    payload_randomized_balance.yaml
    disturbance_recovery.yaml
    one_wheel_balance.yaml
```

Each task config should define:

```text
command distribution
initial state distribution
reward terms and weights
termination conditions
domain randomization profile
curriculum stage
evaluation metrics
```

The training pipeline should be able to run:

```text
single-task specialist training
multi-task command-conditioned training
curriculum training across progressively harder tasks
```


---

## 4. Architectural principle

The most important design rule is:

> The reinforcement learning framework should not depend directly on ROS 2.

Instead, the training system should expose a clean **Gymnasium-compatible environment API**:

```python
obs, info = env.reset()
obs, reward, terminated, truncated, info = env.step(action)
```

Tianshou should interact only with this environment interface.

ROS 2, Gazebo, the custom simulator, serious training simulators, or the real robot
should be hidden behind interchangeable backends.

The intended architecture is:

```text
Tianshou PPO/SAC
        ↓
Tianshou Collector
        ↓
Gymnasium-compatible WheeledBipedEnv
        ↓
Backend interface
        ↓
PythonSimBackend / MuJoCoBackend / BraxMjxBackend / IsaacBackend / Ros2GazeboBackend / RealRobotBackend
        ↓
Simulation or physical robot
```

This makes the training code independent from the simulation or deployment backend.

The simulator stack should be understood as three layers:

```text
foundational layer:
    custom Gymnasium environment
    ad hoc / reduced-DOF linkage simulation
    purpose: formulate the RL problem and prove it is learnable

robusting layer:
    MuJoCo, Brax/MJX, Isaac Lab / Isaac Sim, or another proven training backend
    purpose: improve physics fidelity, contacts, actuator limits, randomization, and scale

validation layer:
    Gazebo + ROS 2
    purpose: validate robot-description compatibility, message flow, sensors, controllers,
             timing, latency, and deployment assumptions
```

Gazebo should therefore be treated primarily as the validation and integration layer.
It should not be the default environment-step factory for PPO/SAC training.

Detailed layer plans:

- [`foundational_layer_plan.md`](../plans/foundational_layer_plan.md)
- [`robusting_layer_plan.md`](../plans/robusting_layer_plan.md)
- [`gazebo_validation_feedback_plan.md`](../plans/gazebo_validation_feedback_plan.md)
- [`model_candidate_versioning_plan.md`](../plans/model_candidate_versioning_plan.md)
- [`controller_candidate_registry_plan.md`](../plans/controller_candidate_registry_plan.md)

---

## 4. Proposed repository architecture

A possible repository structure is:

```text
wheeled-biped-rl/
│
├── README.md
├── pyproject.toml
├── configs/
│   ├── tasks/
│   │   ├── stand_balance.yaml
│   │   ├── velocity_tracking.yaml
│   │   ├── curved_path_tracking.yaml
│   │   ├── payload_randomized_balance.yaml
│   │   ├── disturbance_recovery.yaml
│   │   └── one_wheel_balance.yaml
│   ├── env/
│   │   ├── balance.yaml
│   │   ├── velocity_tracking.yaml
│   │   └── ros2_gazebo.yaml
│   ├── algo/
│   │   ├── ppo.yaml
│   │   └── sac.yaml
│   ├── robot/
│   │   ├── simplified_planar.yaml
│   │   └── robot_limits.yaml
│   ├── real_world/
│   │   ├── domain_randomization.yaml
│   │   ├── deployment_pi.yaml
│   │   ├── evaluation_hard.yaml
│   │   └── evaluation_extreme.yaml
│   └── safety/
│       └── safety_limits.yaml
│
├── src/
│   └── wheeled_biped_rl/
│       ├── envs/
│       │   ├── wheeled_biped_env.py
│       │   ├── observation_builder.py
│       │   ├── reward_builder.py
│       │   ├── action_adapter.py
│       │   └── termination.py
│       │
│       ├── backends/
│       │   ├── base_backend.py
│       │   ├── python_sim_backend.py
│       │   ├── ros2_gazebo_backend.py
│       │   └── real_robot_backend.py
│       │
│       ├── simulation/
│       │   ├── simple_dynamics.py
│       │   ├── robot_state.py
│       │   └── integration.py
│       │
│       ├── policies/
│       │   ├── networks.py
│       │   └── export.py
│       │
│       ├── training/
│       │   ├── train_ppo.py
│       │   ├── train_sac.py
│       │   ├── collectors.py
│       │   └── logging.py
│       │
│       ├── ros2/
│       │   ├── policy_node.py
│       │   ├── ros2_interface.py
│       │   └── message_adapters.py
│       │
│       ├── real_world_effects/
│       │   ├── sensor_model.py
│       │   ├── actuator_model.py
│       │   ├── delay_model.py
│       │   ├── domain_randomizer.py
│       │   └── real_world_wrapper.py
│       │
│       ├── safety/
│       │   ├── safety_supervisor.py
│       │   └── limits.py
│       │
│       ├── deployment/
│       │   ├── raspberry_pi_node.py
│       │   ├── inference_runtime.py
│       │   └── benchmark_policy.py
│       │
│       └── utils/
│           ├── config.py
│           ├── seeding.py
│           └── math_utils.py
│
├── ros2_ws/
│   └── src/
│       └── wheeled_biped_description/
│           ├── urdf/
│           ├── meshes/
│           ├── launch/
│           └── config/
│
├── scripts/
│   ├── train_ppo.py
│   ├── train_sac.py
│   ├── evaluate_policy.py
│   ├── export_policy.py
│   └── benchmark_policy_on_pi.py
│
└── tests/
    ├── test_env_api.py
    ├── test_observation_builder.py
    ├── test_action_adapter.py
    ├── test_reward_builder.py
    ├── test_real_world_effects.py
    └── test_safety_supervisor.py
```

The exact structure can change, but the separation between **environment**, **backend**, **training**, and **ROS 2 deployment** should be preserved.

---

## 5. Environment design

The central environment should be something like:

```python
class WheeledBipedEnv(gym.Env):
    def __init__(self, backend, config):
        self.backend = backend
        self.config = config
        self.observation_space = ...
        self.action_space = ...

    def reset(self, seed=None, options=None):
        super().reset(seed=seed)
        robot_state = self.backend.reset()
        observation = self.observation_builder.build(robot_state)
        return observation, {}

    def step(self, action):
        safe_action = self.action_adapter.process(action)
        robot_state = self.backend.step(safe_action)

        observation = self.observation_builder.build(robot_state)
        reward = self.reward_builder.compute(robot_state, safe_action)
        terminated = self.termination_checker.has_fallen(robot_state)
        truncated = self.termination_checker.has_timed_out(robot_state)
        info = self._build_info(robot_state, reward, safe_action)

        return observation, reward, terminated, truncated, info
```

The environment owns the RL-specific logic:

- observation construction;
- action scaling and clipping;
- reward computation;
- termination logic;
- episode bookkeeping;
- curriculum logic, if added later.

The backend owns the physical or simulated execution:

- reset the robot or simulator;
- apply processed actions;
- advance the simulation or wait for control time;
- return a structured robot state.

---

## 6. Backend abstraction

The backend interface should be explicit and small.

Example:

```python
class BaseBackend(Protocol):
    def reset(self) -> RobotState:
        ...

    def step(self, action: RobotAction) -> RobotState:
        ...

    def close(self) -> None:
        ...
```

The expected backend implementations are:

### 6.1 PythonSimBackend

Used for fast early experiments.

Responsibilities:

- simulate reduced-order wheeled-biped dynamics;
- model the constrained leg linkage through explicit kinematics/dynamics, not as an
  independently actuated serial hip/knee tree;
- support fast environment stepping;
- allow vectorized training where possible;
- inject noise, latency, saturation, and domain randomization;
- expose the same state variables that would be available from real sensors.

This backend is ideal for first PPO/SAC experiments.

### 6.2 Physics training backends

Used after the reduced Python environment proves that the RL formulation is coherent.

The serious training backend should not be chosen only by preference. The constrained
leg linkage is a first-order modelling risk, so the repository should run small
feasibility tests before committing to one simulator.

Candidate backends:

```text
MuJoCo / MJCF
Brax / MJX
Isaac Lab / Isaac Sim
Gazebo / SDF
```

The feasibility tests should build the same minimal linkage in each candidate and
compare:

- constraint accuracy and numerical stability;
- stepping speed and parallelism;
- contact, friction, and actuator-limit support;
- ease of modelling the passive/constrained linkage;
- ease of preserving the same observation/action contract as `WheeledBipedEnv`;
- tooling burden and reproducibility.

Likely roles:

- **MuJoCo** is a strong candidate for constrained mechanisms and fast RL iteration.
- **Brax / MJX** are candidates when JAX-based vectorized training is attractive,
  especially if the linkage can be represented with acceptable constraint fidelity.
- **Isaac Lab / Isaac Sim** is a strong candidate when GPU-parallel scale, contact-rich
  training, terrain, or large domain-randomized batches become necessary.
- **Gazebo / SDF** is valuable for robotics-stack validation and may be used for
  feasibility testing, but it should not be assumed to be the main RL step factory.

NVIDIA GPU access is not guaranteed. The architecture should therefore keep a
CPU-friendly path viable through the reduced Python environment and/or MuJoCo. Brax /
MJX and Isaac Lab / Isaac Sim should be treated as high-value options when their
hardware/runtime requirements are available and their linkage modelling is proven, not
as hard dependencies for the project.

The training-facing interface should remain conceptually stable:

```text
observation -> policy -> action -> env.step(action)
```

The simulator behind `env.step` may change, but PPO/SAC should not be rewritten around a
specific simulator.

### 6.3 Ros2GazeboBackend

Used for high-fidelity validation and ROS 2 integration, not as the default RL inner
loop.

Responsibilities:

- launch or connect to a ROS 2 simulation stack;
- publish processed actions as ROS 2 commands;
- read `/joint_states`, IMU, odometry, TF, and controller state topics;
- reset the simulator;
- step or synchronize simulation time;
- translate ROS 2 messages into the internal `RobotState` structure.

This backend should validate that a policy trained in the faster simulator can survive
the ROS 2 integration stack: message flow, robot description compatibility, sensors,
controllers, timing, latency, and deployment assumptions.

Gazebo should not be the environment-step factory for ordinary PPO/SAC training unless
the simulator feasibility tests show that it is the best available option for this
mechanism and workload.

### 6.4 RealRobotBackend

Used only for cautious evaluation or deployment, not unsafe online training.

Responsibilities:

- read real sensor data;
- send safe commands to controllers;
- enforce limits and emergency stops;
- never allow raw policy output to command hardware directly;
- support policy evaluation under strict safety constraints.

For real hardware, the preferred deployment mode is not necessarily `env.step()` training. Instead, a trained policy should be exported and run in a dedicated ROS 2 policy node.

---

## 7. Observation design

The observation should contain only quantities that are available or realistically estimable on the real robot. The policy should not depend on perfect simulator-only state unless that information is used only by a critic, teacher, or privileged-training mechanism and is removed from the deployed actor.

The proposed observation structure is aligned with common legged-RL practice, where policies often receive:

```text
base orientation or projected gravity
base angular velocity
joint positions
joint velocities
actuator or wheel velocities
previous action
command targets
optional terrain or height measurements
optional privileged training-only states
```

A useful reference pattern is the `legged_gym` observation structure, which concatenates base linear velocity, base angular velocity, projected gravity, commands, DOF positions, DOF velocities, previous actions, optional terrain height measurements, and optional observation noise. For this robot, the exact terms should be adapted to wheeled-biped dynamics and real deployability.

### 7.1 Prefer projected gravity over raw Euler angles where possible

For internal policy input, projected gravity is often preferable to raw pitch/roll Euler angles because it represents body orientation relative to gravity without relying directly on Euler-angle conventions.

Recommended deployable orientation-related terms:

```text
projected_gravity_x
projected_gravity_y
projected_gravity_z
gyro_x
gyro_y
gyro_z
```

Pitch and roll should still be logged for debugging because they are easy to interpret, but the policy input can use projected gravity plus angular velocity.

### 7.2 Initial deployable observation vector

A reasonable first deployable observation for this robot is:

```text
observation = [
    projected_gravity_x,
    projected_gravity_y,
    projected_gravity_z,

    gyro_x,
    gyro_y,
    gyro_z,

    left_leg_joint_positions,
    right_leg_joint_positions,

    left_leg_joint_velocities,
    right_leg_joint_velocities,

    left_wheel_velocity,
    right_wheel_velocity,

    previous_action,

    target_forward_velocity,
    target_yaw_rate,
    target_body_height,

    battery_voltage_normalized
]
```

Optional later terms:

```text
estimated_payload_mass
estimated_payload_com_offset
target_roll_angle
balance_mode_id
terrain_height_samples
estimated_body_height
estimated_forward_velocity
```

For early planar simulation, a reduced observation may be enough:

```text
body pitch or projected gravity
body pitch velocity
left wheel velocity
right wheel velocity
left leg configuration
right leg configuration
forward velocity estimate
commanded forward velocity
previous action
```

### 7.3 Deployable observations vs privileged observations

The repo should explicitly separate **deployable observations** from **privileged training-only observations**.

Deployable observations are available on the Raspberry Pi or can be estimated reliably from real sensors:

```text
IMU orientation estimate or projected gravity
IMU angular velocity
joint encoder positions
joint encoder velocities
wheel encoder velocities
previous action
command vector
battery voltage
optional payload estimate
```

Privileged observations are available in simulation but should not be fed to the deployed actor unless the real robot can estimate them robustly:

```text
true base linear velocity
true centre of mass
exact payload mass
exact payload centre-of-mass offset
exact friction coefficient
exact ground slope
contact forces
noiseless full state
```

The repository may later support asymmetric actor-critic training, where the critic receives privileged information during training but the actor receives only deployable observations.

### 7.4 Command-conditioned observation

Because the robot should learn more than static self-balance, the command vector should be part of the observation.

Initial command vector:

```text
command = [
    target_forward_velocity,
    target_yaw_rate,
    target_body_height
]
```

Later command vector:

```text
command = [
    target_forward_velocity,
    target_yaw_rate,
    target_body_height,
    target_roll_angle,
    target_pitch_offset,
    balance_mode_id,
    estimated_payload_mass
]
```

This enables the same policy to learn standing, straight-line motion, curved motion, turning, height adaptation, and payload compensation as variations of command tracking.

### 7.5 Practical warning

Do not include a state term just because the simulator can provide it. If the real Raspberry Pi controller cannot measure or estimate it with similar delay, noise, and reliability, it should either be excluded from the actor observation or treated as privileged training-only information.


---

## 8. Action design

The first implementation should avoid raw motor torques unless the simulator, actuator model, and low-level control are already reliable.

Preferred initial action space:

```text
left wheel velocity target
right wheel velocity target
left leg length or posture target
right leg length or posture target
optional body pitch target or residual correction
```

Alternative lower-level action space:

```text
left wheel torque
right wheel torque
left hip torque
left knee torque
right hip torque
right knee torque
```

The lower-level torque action space is more expressive but harder to train and riskier for sim-to-real transfer.

The recommended first approach is:

```text
RL policy
    ↓
high-level action targets
    ↓
action adapter
    ↓
position/velocity/torque references
    ↓
low-level controller
```

The action adapter should handle:

- scaling from normalized `[-1, 1]` actions;
- clipping to physical limits;
- action smoothing;
- rate limits;
- conversion from high-level targets to controller references;
- safety checks.

---

## 9. Reward design

Reward design should be incremental and testable.

For the initial balance task:

```text
+ upright body posture
- pitch error
- pitch angular velocity
- excessive wheel velocity
- excessive action magnitude
- excessive action rate
- joint limit violation
- fall event
```

For velocity tracking:

```text
+ commanded velocity tracking
+ upright body posture
+ stable body height
- velocity tracking error
- angular velocity instability
- energy usage
- action rate
- wheel slip
- joint limit violation
- fall event
```

A simple first reward could be:

```text
reward = upright_reward
       + velocity_tracking_reward
       + height_reward
       - action_penalty
       - action_rate_penalty
       - energy_penalty
       - joint_limit_penalty
       - fall_penalty
```

The implementation should log each reward component separately. This is important because a single scalar reward is hard to debug.

---

## 10. Termination and truncation

Episodes should terminate when the robot clearly fails.

Possible termination conditions:

```text
absolute pitch exceeds threshold
absolute roll exceeds threshold
body height below minimum
joint limit violation beyond safety margin
simulator instability
non-finite state values
```

Episodes should be truncated when:

```text
maximum episode length is reached
curriculum stage timeout is reached
```

Termination and truncation should be handled separately according to the Gymnasium API.

---

## 11. Tianshou training architecture

Tianshou should be the RL framework used to train PPO and SAC.

The expected training flow is:

```text
create config
create environment factory
create vectorized train environments
create vectorized test environments
create actor/critic networks
create Tianshou policy
create collector
create trainer
train
save checkpoints
export final actor
```

Conceptual PPO flow:

```text
PPOPolicy
    ↓
Collector collects fresh rollouts
    ↓
On-policy update
    ↓
Evaluation
    ↓
Checkpoint
```

Conceptual SAC flow:

```text
SACPolicy
    ↓
Collector gathers transitions
    ↓
ReplayBuffer stores experience
    ↓
Off-policy updates
    ↓
Evaluation
    ↓
Checkpoint
```

Initial recommendation:

1. implement PPO first;
2. validate the environment and reward;
3. add SAC after the environment is stable.

PPO is usually the safer first algorithm because it is comparatively robust for locomotion-style control. SAC may become useful later for continuous control and sample efficiency, but it is more sensitive to reward scale, entropy settings, and action scaling.

---

## 12. ROS 2 role

ROS 2 should be treated as the robotics integration and deployment layer, not the
learning algorithm and not the default RL environment-step factory.

ROS 2 can provide:

- standard communication between robot components;
- topics, services, and actions;
- logging with rosbag;
- visualization through RViz;
- robot description through URDF/Xacro;
- simulation integration with Gazebo or other validation simulators;
- `ros2_control` for hardware and controller abstraction;
- deployment of the trained policy as a ROS 2 node.

ROS 2 should not be placed directly inside the PPO/SAC logic. Instead, it should be hidden behind:

```text
Ros2GazeboBackend
RealRobotBackend
ROS2PolicyNode
```

The final deployment architecture should look like:

```text
trained PyTorch actor
        ↓
ROS 2 policy node
        ↓
safety/action adapter
        ↓
ros2_control controller interface
        ↓
motor drivers
        ↓
physical robot
```

The policy node should subscribe to sensor/state topics and publish safe controller references.

Example ROS 2 topics may include:

```text
/joint_states
/imu
/odom
/tf
/controller_state
/policy_action
/controller_commands
/robot_status
/emergency_stop
```

Gazebo + ROS 2 should primarily answer integration questions:

```text
Does the robot description load correctly?
Do messages, transforms, sensors, and controllers connect correctly?
Does the trained policy survive realistic timing, latency, and controller assumptions?
Does the deployment path match what was trained?
```

The RL inner loop should remain ROS-free and run through a fast Gymnasium-compatible
environment or a training backend selected from the simulator feasibility tests.

---

## 13. Sim-to-real considerations

The simplified Python simulator should not be trusted blindly.

Potential sim-to-real gaps include:

```text
wheel slip
contact modelling errors
motor saturation
latency
sensor noise
IMU drift
encoder quantization
backlash
compliance
battery voltage variation
centre-of-mass modelling error
linkage kinematics mismatch
```

The training pipeline should support:

- domain randomization;
- observation noise;
- action delay;
- actuator limits;
- action smoothing;
- random mass/inertia perturbations;
- random friction coefficients;
- random initial pitch and velocity;
- curriculum learning.

The policy should never depend on perfect simulator-only information.

---

## 14. Linkage and kinematic warning

The target robot appears to use nontrivial hip/knee linkage mechanisms. This matters.

A simple two-joint leg model may not be accurate enough if the real robot uses crank links or nonlinear mechanical transmission.

The implementation should separate:

```text
policy action
    ↓
kinematic/action adapter
    ↓
actual motor references
```

The policy may output intuitive high-level targets such as leg length, body height, or posture, while the adapter converts these into motor positions, velocities, or torques.

This avoids forcing the policy to learn mechanical linkage details directly during early experiments.

---


## 21. Deployment-aware training and Raspberry Pi constraints

The policies trained in this repository are intended to be deployed on a **Raspberry Pi board** that controls the physical wheeled-biped robot. This is a first-class requirement, not a later deployment detail.

The goal is therefore not merely:

```text
train a policy that works in simulation
```

The real goal is:

```text
train a policy that remains stable when executed on embedded hardware controlling a real robot with imperfect sensors, actuators, timing, and mechanics
```

A naive simulator may expose the policy to:

```text
perfect state
zero-latency actions
ideal motors
instantaneous torque or velocity response
no sensor noise
no wheel slip
no battery voltage drop
no missed control cycles
unlimited compute
perfect reset conditions
```

The physical robot will instead expose the policy to:

```text
delayed IMU measurements
encoder quantization
motor saturation
control-loop jitter
wheel slip
backlash and compliance
battery-dependent torque limits
model inference latency
noisy velocity estimates
imperfect centre-of-mass modelling
mechanical asymmetry
thermal limits
occasional bad sensor packets
```

The repository should therefore include a **real-world effects layer** between the ideal simulator and the RL environment interface.

Conceptually:

```text
Tianshou PPO/SAC
        ↓
Gymnasium WheeledBipedEnv
        ↓
RealWorldEffectsWrapper
        ↓
Simulation backend
        ↓
Robot dynamics model
```

The simulator does not need to be perfectly accurate. Instead, the training process should expose the policy to a family of plausible real-world conditions so that the final controller is less brittle when moved to the physical robot.

---

## 22. Real-world effects layer

The real-world effects layer should be configurable and reusable across the Python simulator and the ROS 2/Gazebo backend where possible.

A useful abstraction is:

```python
class RealWorldEffectsWrapper(gym.Wrapper):
    def __init__(
        self,
        env,
        sensor_model,
        actuator_model,
        delay_model,
        domain_randomizer,
        safety_supervisor,
    ):
        ...
```

The wrapper should transform an ideal environment into a deployment-aware environment:

```text
IdealWheeledBipedEnv
        ↓
RealWorldEffectsWrapper
        ↓
Tianshou Collector
```

A realistic training step should approximate the deployed control path:

```python
raw_state = simulator.step_physics()
sensor_data = sensor_model.apply(raw_state)
delayed_sensor_data = delay_model.apply_observation_delay(sensor_data)
observation = observation_builder.build(delayed_sensor_data)

raw_action = policy(observation)
safe_action = action_adapter.process(raw_action)
safe_action = safety_supervisor.filter(safe_action, observation)
delayed_action = delay_model.apply_action_delay(safe_action)
actuated_command = actuator_model.apply(delayed_action)
simulator.apply(actuated_command)
```

The following effects should be supported.

### 16.1 Sensor noise, bias, drift, and quantization

The robot should not receive perfect simulator state. The environment should support configurable models for:

```text
IMU noise
gyroscope bias
accelerometer bias
orientation filter lag
encoder quantization
velocity estimate noise
sensor drift
occasional sensor packet drops
```

Important distinctions:

```text
noise: random error
bias: systematic offset
drift: slowly changing error
delay: old information
dropout: missing information
```

For a balancing robot, IMU quality and timing are especially important. The policy should be trained on observations that resemble the state estimates available on the Raspberry Pi, not on perfect hidden simulator state.

### 16.2 Observation and action delay

The Raspberry Pi will not receive sensor data or apply motor commands instantaneously.

The environment should support configurable delay buffers:

```text
imu_delay_ms
encoder_delay_ms
velocity_estimation_delay_ms
observation_pipeline_delay_ms
action_delay_ms
motor_driver_delay_ms
```

A simple approximation is to use queues:

```text
sensor value at time t
        ↓
observation delay buffer
        ↓
policy receives value from t - delay
```

and:

```text
policy action at time t
        ↓
action delay buffer
        ↓
actuator receives action from t - delay
```

This is critical for a wheeled-biped robot because balance controllers are highly sensitive to latency.

### 16.3 Actuator dynamics and saturation

The real motors cannot generate arbitrary torque, speed, acceleration, or instantaneous response.

The environment should model:

```text
maximum motor torque
maximum motor velocity
maximum joint velocity
maximum wheel acceleration
maximum current
motor response time constant
thermal derating
battery-voltage derating
action rate limits
```

The action path should be:

```text
policy output in [-1, 1]
        ↓
scale to physical command range
        ↓
clip to safe limits
        ↓
apply rate limits
        ↓
apply actuator dynamics
        ↓
send to simulated or real controller
```

The policy should learn within these limits instead of discovering them only during hardware deployment.

### 16.4 Control-loop timing and jitter

The repo should distinguish between:

```text
physics timestep
low-level controller timestep
policy timestep
sensor update timestep
logging timestep
```

A plausible configuration may be:

```text
physics:          500-1000 Hz
low-level PID:    100-500 Hz
policy:            25-100 Hz
logging:            5-20 Hz
```

The policy should be trained at the same control frequency expected during Raspberry Pi deployment, or under a randomized frequency range around it.

The environment should support:

```text
control_period_jitter_ms
missed_action_probability
command_hold_steps
```

This helps prevent policies that only work under ideal fixed-timestep simulation.

### 16.5 Mass, inertia, and centre-of-mass uncertainty

The real robot's mass distribution will not exactly match the simulator. Batteries, printed parts, fasteners, wiring, wheels, and motor placement can all shift the centre of mass.

The training pipeline should support domain randomization for:

```text
body mass
leg mass
wheel mass
link inertia
motor inertia
centre-of-mass position
payload mass
wheel radius
joint friction
```

Example ranges:

```yaml
mass_randomization:
    body_mass_scale: [0.9, 1.1]
    leg_mass_scale: [0.9, 1.1]
    wheel_mass_scale: [0.95, 1.05]

center_of_mass_randomization:
    com_x_offset_m: [-0.02, 0.02]
    com_z_offset_m: [-0.02, 0.02]

geometry_randomization:
    wheel_radius_scale: [0.97, 1.03]
```

### 16.6 Friction, wheel slip, and ground conditions

The robot depends heavily on wheel-ground interaction. The training environment should randomize:

```text
ground friction
rolling resistance
wheel slip
floor slope
small bumps
contact stiffness
contact damping
```

A simple early approximation can be:

```text
effective_wheel_force = ideal_wheel_force * slip_factor
```

Later, a higher-fidelity backend such as Gazebo can randomize contact parameters directly.

### 16.7 Battery and power constraints

The policy should not rely on unlimited power.

The environment should support modelling:

```text
battery voltage
voltage-dependent maximum torque
current limits
power budget
brownout risk
```

A simple approximation is:

```text
available_torque = nominal_torque * battery_voltage_factor
```

Battery state can also be logged during evaluation to detect policies that require unrealistic power.

---

## 23. Raspberry Pi deployment requirements

The trained policy should eventually be embedded onto a Raspberry Pi. This creates additional constraints on model size, inference time, runtime dependencies, and control-loop reliability.

The repo should support export to at least one lightweight inference format:

```text
PyTorch state_dict
TorchScript
ONNX
```

The initial policy network should be intentionally compact. Suitable first actor networks are likely:

```text
observation_dim → 64 → 64 → action_dim
```

or:

```text
observation_dim → 128 → 128 → action_dim
```

Large networks should be avoided until the Raspberry Pi inference budget is measured.

The deployment loop should mirror the training loop:

```text
read sensors
        ↓
build observation
        ↓
normalize observation
        ↓
run policy inference
        ↓
scale action
        ↓
apply safety limits
        ↓
send command to motor controllers
        ↓
log data
```

Critical rule:

> The same observation builder, action adapter, normalization logic, and safety supervisor should be reused between training and Raspberry Pi deployment.

Duplicating these components separately for training and deployment risks training one problem and deploying another.

The repo should include a Raspberry Pi benchmark command, for example:

```bash
python -m wheeled_biped_rl.deployment.benchmark_policy \
    --model checkpoints/policy.onnx \
    --obs-dim 32 \
    --action-dim 6 \
    --frequency 50
```

The benchmark should report:

```text
mean inference time
p95 inference time
p99 inference time
maximum inference time
control deadline misses
CPU usage
memory usage
model size
```

A model that performs well in training but misses its control-loop deadline on the Raspberry Pi is not deployable.

---

## 24. Domain randomization and evaluation profiles

The repo should make domain randomization configurable through YAML files.

Example:

```yaml
domain_randomization:
    enabled: true

    sensors:
        imu_delay_ms: [5, 30]
        encoder_delay_ms: [2, 15]
        gyro_noise_std: [0.001, 0.02]
        pitch_noise_std: [0.001, 0.01]

    actuators:
        action_delay_ms: [5, 40]
        torque_scale: [0.75, 1.0]
        motor_time_constant_s: [0.02, 0.08]

    mass:
        body_scale: [0.9, 1.1]
        leg_scale: [0.9, 1.1]
        wheel_scale: [0.95, 1.05]

    center_of_mass:
        x_offset_m: [-0.02, 0.02]
        z_offset_m: [-0.02, 0.02]

    ground:
        friction: [0.5, 1.2]
        slope_deg: [-3.0, 3.0]
        rolling_resistance: [0.001, 0.02]

    control_loop:
        policy_frequency_hz: [40, 60]
        jitter_ms: [0, 5]
        missed_action_probability: [0.0, 0.02]
```

Training should be staged. Do not randomize every imperfection from day one.

Recommended progression:

```text
Stage 1: ideal simulation for basic upright balance
Stage 2: actuator limits and action smoothing
Stage 3: sensor noise and moderate delay
Stage 4: mass, inertia, and centre-of-mass randomization
Stage 5: ground friction and slip randomization
Stage 6: full deployment-like constraints
Stage 7: frozen-policy evaluation under harsher unseen conditions
```

Evaluation should be harsher than training. The repo should support separate profiles:

```text
training_randomization.yaml
evaluation_nominal.yaml
evaluation_hard.yaml
evaluation_extreme.yaml
deployment_pi.yaml
```

Evaluation metrics should include:

```text
fall rate
mean survival time
velocity tracking error
pitch RMS error
body height error
energy usage
action smoothness
maximum motor command
control deadline miss tolerance
recovery from disturbance
recovery from small floor slope
recovery from small push
```

For this robot, simply avoiding a fall is not sufficient. The policy should also avoid aggressive, hardware-damaging, high-energy behaviours.

---

## 25. Safety layer

The deployed Raspberry Pi must not send raw policy outputs directly to motor drivers.

The runtime command path should be:

```text
policy action
        ↓
action adapter
        ↓
safety supervisor
        ↓
low-level controller
        ↓
motor driver
```

The safety supervisor should enforce:

```text
joint limits
wheel speed limits
torque/current limits
body pitch emergency cutoff
body roll emergency cutoff
battery voltage cutoff
temperature cutoff
communication timeout
manual emergency stop
```

During training, the same safety rules should be simulated when possible. Otherwise, the policy may learn actions that deployment will later block, creating a training/deployment mismatch.

Important deployment principle:

> The policy should suggest commands; the safety layer decides whether those commands are allowed.

---

## 20. Practical warning about overengineering

The repo should be designed for deployment-aware training, but it should not try to model every real-world imperfection perfectly in the first version.

A bad or overly aggressive randomization setup can make training unstable and obscure whether the basic control formulation is correct.

The recommended approach is:

```text
first build a simple working PPO pipeline
then add one real-world imperfection at a time
then measure whether robustness improves
```

For this robot, the highest-priority real-world effects are likely:

```text
1. action delay
2. IMU delay and noise
3. motor saturation
4. action-rate limits
5. centre-of-mass uncertainty
6. wheel-ground friction and slip
7. control-loop jitter
8. battery-dependent torque loss
```

These should be implemented before spending too much effort on lower-priority realism.

---

## 21. Development phases

Recommended implementation sequence:

### Phase 1: Mechanism analysis

- Identify true degrees of freedom.
- Define loop-closure constraints.
- Define actuator inputs and passive states.
- Define output coordinates such as leg length, wheel/contact pose, and body height.
- Define the measurable state available to the deployable actor.

### Phase 2: Minimal Python environment

- Implement `WheeledBipedEnv`.
- Implement `PythonSimBackend`.
- Implement reduced-order linkage kinematics/dynamics.
- Do not model the mechanism as an independently actuated serial hip/knee tree.
- Train PPO for balance in place.
- Log reward components and state variables.

### Phase 3: Velocity tracking

- Add commanded forward velocity.
- Extend observation space.
- Add velocity tracking reward.
- Add randomized commands.

### Phase 4: Robustness

- Add noise, latency, saturation, and randomization.
- Add action smoothing and rate limits.
- Add curriculum learning.

### Phase 5: Physics backend feasibility tests

- Build the same minimal linkage in MuJoCo/MJCF.
- Build the same minimal linkage in Brax/MJX if JAX-based training is a serious option.
- Build the same minimal linkage in Gazebo/SDF.
- Optionally build the same minimal linkage in Isaac Lab / Isaac Sim.
- Compare stability, speed, constraint accuracy, contact/friction support, actuator
  modelling, and implementation burden.
- Pick the serious training backend from evidence, not assumption.

### Phase 6: Serious training backend

- If MuJoCo handles the linkage well, use MuJoCo for higher-fidelity RL training.
- If Brax/MJX handles the linkage well and JAX vectorization is useful, use it for
  large-batch training experiments.
- If Isaac handles the linkage robustly and massive parallelism is needed, use Isaac
  Lab / Isaac Sim.
- Do not make Isaac a hard dependency unless NVIDIA GPU access is confirmed.
- If neither is robust enough, keep reduced-order training and use Gazebo only for
  validation.
- Preserve the same conceptual observation/action interface used by the simple
  Gymnasium environment.

### Phase 7: ROS 2 / Gazebo validation

- Add robot description package.
- Add Gazebo/SDF or simulator integration for validation.
- Add ROS 2 message adapters.
- Add `Ros2GazeboBackend`.
- Validate trained policies in the robotics integration stack.

### Phase 8: Policy export and ROS 2 deployment

- Export trained PyTorch actor.
- Implement `policy_node.py`.
- Subscribe to robot state topics.
- Publish safe controller references.
- Integrate with `ros2_control`.

### Phase 9: Real robot evaluation

- Add strict safety constraints.
- Test on supports or with emergency stop.
- Evaluate balance only before locomotion.
- Increase policy authority gradually.

---

## 22. What the first repository version should implement

The first useful version of the repository should implement:

```text
Gymnasium-compatible WheeledBipedEnv
PythonSimBackend
RobotState dataclass
RobotAction dataclass
ObservationBuilder
ActionAdapter
RewardBuilder
TerminationChecker
Tianshou PPO training script
evaluation script
configuration files
basic tests for env.step/reset
```

It does not need full ROS 2 support immediately, but the abstractions should be designed so that ROS 2 can be added later without rewriting the training code.

The first success criterion should be:

> PPO can train a policy that keeps a simplified wheeled-biped model upright for a full episode while respecting action and joint limits.

The second success criterion should be:

> The same environment can train velocity tracking with randomized forward velocity commands.

---

## 23. Non-goals for the first version

The first implementation should not attempt to solve everything.

Initial non-goals:

```text
full 3D robot simulation
raw torque control on all actuators
real hardware training
advanced terrain traversal
vision-based observations
full ROS 2 launch stack
complex Gazebo integration
online learning on the physical robot
```

These can be added later after the basic RL loop is validated.

---

## 24. Key design decisions

The repository should follow these decisions:

1. Use **Tianshou** as the RL framework.
2. Use **Gymnasium** as the environment API.
3. Keep PPO/SAC independent from ROS 2.
4. Use backend abstraction for Python simulation, physics training backends, ROS 2
   validation, and real robot integration.
5. Start with mechanism analysis and a reduced-order Python Gymnasium environment.
6. Do not model the constrained leg linkage as an independently actuated serial tree.
7. Run feasibility tests in MuJoCo/MJCF, Brax/MJX, Gazebo/SDF, and optionally Isaac
   Lab / Isaac Sim before choosing the serious training backend.
8. Keep a CPU-friendly training path because NVIDIA GPU access is not guaranteed.
9. Treat Gazebo + ROS 2 as validation and deployment integration by default, not as the
   main RL training loop.
10. Add ROS 2 later as a validation and deployment layer.
11. Do not command real motors directly from raw policy output.
12. Use an action adapter and safety layer.
13. Log reward components separately.
14. Keep observations realistic and sensor-compatible.
15. Design for sim-to-real from the beginning, but do not overcomplicate the first version.

---

## Reference notes for observation and control design

The design above is intended to follow common patterns from legged and wheeled-legged RL rather than inventing a completely new observation/control formulation.

Useful references for the implementation agent:

1. `legged_gym` observation construction is a practical open-source reference. Its base legged-robot environment constructs observations from base linear velocity, base angular velocity, projected gravity, command vector, joint positions, joint velocities, previous actions, optional terrain height measurements, and optional observation noise. This supports the proposed use of projected gravity, angular velocity, joint states, commands, previous actions, and optional terrain terms.

   URL: `https://github.com/leggedrobotics/legged_gym/blob/master/legged_gym/envs/base/legged_robot.py`

2. The paper *Learning Robust Autonomous Navigation and Locomotion for Wheeled-Legged Robots* presents a hierarchical RL system for wheeled-legged robots, combining locomotion control with higher-level navigation. This supports the proposed architecture where a high-level planner or command generator feeds a lower-level command-conditioned locomotion policy.

   URL: `https://arxiv.org/abs/2405.01792`

3. The broader legged-locomotion RL literature commonly uses command-conditioned policies for velocity tracking. The relevant pattern for this project is to condition the low-level policy on target forward velocity, yaw rate, and body/posture commands rather than training a separate policy for every straight or curved trajectory.

Implementation implication:

```text
Use the literature/repo patterns as design guidance, but keep the final observation vector constrained by what the physical Raspberry Pi robot can actually measure or estimate.
```


---

## 25. Summary

This repository should implement a modular RL training pipeline for a wheeled-biped balancing robot.

The core stack is:

```text
Tianshou
    ↓
Gymnasium WheeledBipedEnv
    ↓
Backend abstraction
    ↓
Python simulator first
    ↓
ROS 2 / Gazebo later
    ↓
ROS 2 policy deployment on the real robot
```

The immediate goal is not to build a complete robot stack. The immediate goal is to create a clean, testable training pipeline where PPO can first learn balance and simple velocity tracking in a simplified environment, then evolve toward a compact command-conditioned generalist locomotion policy.

The long-term architecture should pair this generalist policy with hierarchical control: a high-level planner or behaviour manager generates commands, while the learned policy handles low-level balance, posture, and locomotion. Specialist policies may be added for genuinely distinct or risky behaviours, but the default should not be one separate model per normal movement type.

The architecture should keep the learning system, simulator backend, ROS 2 deployment path, safety layer, and policy-management layer separated so that the project can evolve from fast Python experimentation to realistic simulation and eventually physical robot control.
