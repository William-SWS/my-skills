# Chapter 18: Reinforcement Learning

## Core Idea
An **agent** observes an **environment**, takes **actions**, and gets **rewards**; it learns a **policy** maximizing expected discounted return. Two main families: **policy gradients** (REINFORCE: directly push up the probability of actions with positive advantage) and **value-based** methods (MDPs, Bellman equations, value/Q-value iteration, TD learning, **Q-learning**, **Deep Q-Networks** with replay buffers, target networks, double/dueling DQN, prioritized replay). The chapter ends with AlphaGo, actor-critics (A2C/A3C, SAC, PPO), curiosity and open-ended learning. Warning: "RL must be forced to work."

## Frameworks Introduced
- **RL setting**: agent, environment, observation, action, reward (possibly only negative, e.g. maze steps). Examples: robots, Ms. Pac-Man, Go, thermostats, trading.
- **Policy search options**: brute force over parameters, **genetic algorithms** (keep the best policies, mutate them; e.g. NEAT), or **policy gradients** (gradient ascent on expected reward).
- **OpenAI Gym API**: `env = gym.make("CartPole-v1", render_mode="rgb_array")`; `obs, info = env.reset(seed=42)`; `obs, reward, done, truncated, info = env.step(action)`; `env.action_space` (e.g. `Discrete(2)`); `env.close()`.
- **Stochastic NN policy**: output action probabilities and **sample** from them (balances exploration vs exploitation; e.g. trying a new restaurant).
- **Credit assignment problem**: rewards are sparse and delayed. **Return** = sum of discounted future rewards with γ (0.9 means ~10 steps matter; 0.99 means ~100). **Action advantage** = normalized return (subtract mean, divide by std over many episodes).
- **REINFORCE (Williams 1992)**:
  1. Play several episodes, computing (but not applying) the gradients that would make each chosen action more likely.
  2. Compute each action's normalized advantage.
  3. Multiply each gradient by its advantage (positive: reinforce; negative: discourage).
  4. Average and apply.
  - It's sample-inefficient, which motivates actor-critics.
- **Markov chains → Markov Decision Processes (MDPs)**: states, actions, transition probabilities T(s, a, s′), rewards R(s, a, s′).
- **Bellman optimality equation**: V*(s) = maxₐ Σₛ′ T(s,a,s′)[R(s,a,s′) + γV*(s′)]. **Value iteration** (dynamic programming) and **Q-value iteration**: Q_{k+1}(s,a) ← Σ T[R + γ maxₐ′ Q_k(s′,a′)]; π*(s) = argmaxₐ Q*(s, a).
- **Temporal Difference (TD) learning**: V(s) ←α r + γV(s′) (TD target; TD error δ). Like SGD, one sample at a time; decay the learning rate.
- **Q-learning (off-policy)**: Q(s,a) ←α r + γ maxₐ′ Q(s′,a′). It learns the optimal (greedy) policy while following any exploration policy.
- **Exploration policies**: **ε-greedy** (random with probability ε, decayed e.g. 1 → 0.05); exploration functions f(Q, N) = Q + κ/(1 + N) (curiosity bonus for rarely tried actions).
- **Approximate / Deep Q-learning (DQN)**: a neural net Q_θ(s) outputs one Q-value per action. Target y = r + γ·maxₐ′ Q_θ(s′, a′) (0 if done). Minimize MSE/Huber on the chosen action's Q (mask with `tf.one_hot(actions)`). **Replay buffer** (`deque(maxlen=2000)`) decorrelates samples.
- **DQN stabilizers**:
  - **Fixed Q-value targets**: a separate target network, synced every N episodes (DeepMind 2013 used 10,000 steps), which stops the "dog chasing its own tail".
  - **Double DQN**: the online net *selects* the best next action and the target net *evaluates* it, reducing overestimation.
  - **Prioritized Experience Replay (PER)**: sample proportional to |TD error|^ζ, with importance-sampling weights (β annealed to 1) to correct the bias.
  - **Dueling DQN**: Q(s,a) = V(s) + A(s,a) − maxₐ′ A(s,a′).
  - **Rainbow** combines six improvements.
- **Other algorithms**: **AlphaGo/AlphaZero/MuZero** (MCTS + deep nets, self-play); **actor-critic** (policy net learns from the critic's Q estimates); **A3C/A2C** (parallel agents; async/sync); **SAC** (maximize reward + entropy, sample efficient); **PPO** (clipped loss, stable; OpenAI Five); **curiosity-based exploration** (reward prediction error of the agent's own model); **open-ended learning** (POET).

## Key Concepts
- **Policy π**: maps observations to actions (deterministic or stochastic).
- **Discount factor γ**; **episode**; **done vs truncated** (a time limit isn't a true terminal state).
- **On-policy vs off-policy**: PG/PPO learn the policy being executed; Q-learning learns the greedy policy from exploratory data.
- **Catastrophic forgetting**: learning new experiences erases old skills, so DQN performance collapses after peaking (episode ~320 in CartPole).
- **Loss is a poor RL progress indicator**: plot total reward per episode instead.
- **Dynamic programming**: break a problem into tractable subproblems (value iteration).

## Mental Models
- Think of the **return as delayed credit**: a good action followed by bad luck gets a low return, but averaged over many episodes good actions win ("a good actor in a terrible movie").
- **Discounting = patience**: in the toy MDP, γ = 0.90 keeps the agent away from the fire (−50) in s1; at γ = 0.95 it goes through the fire for the +40 later.
- **DQN self-targeting is unstable**: anchor the targets (target net), decouple selection from evaluation (double), decorrelate data (replay), focus on surprises (PER).
- **"Supervised learning wants to work; RL must be forced to work"** (Karpathy): expect hyperparameter and seed sensitivity; inject prior knowledge (reward shaping, hand-crafted features) unless you're writing a paper.

## Anti-patterns
- **Greedy (argmax) policies during training**: no exploration.
- **Training on consecutive correlated experiences**: use a replay buffer.
- **Monitoring the loss instead of the rewards**.
- **Treating `truncated` like `done`** in the target computation (the book's simple code masks both; be careful with time limits).
- **Expecting monotonic progress**: save the best-performing weights.
- **Using pure random exploration in big MDPs**: too slow; use ε-decay or curiosity.

## Code Examples
```python
def play_one_step(env, obs, model, loss_fn):              # REINFORCE step
    with tf.GradientTape() as tape:
        left_proba = model(obs[np.newaxis])
        action = (tf.random.uniform([1, 1]) > left_proba)
        y_target = tf.constant([[1.]]) - tf.cast(action, tf.float32)
        loss = tf.reduce_mean(loss_fn(y_target, left_proba))
    grads = tape.gradient(loss, model.trainable_variables)
    obs, reward, done, truncated, info = env.step(int(action))
    return obs, reward, done, truncated, grads

def discount_rewards(rewards, discount_factor):
    discounted = np.array(rewards)
    for step in range(len(rewards) - 2, -1, -1):
        discounted[step] += discounted[step + 1] * discount_factor
    return discounted
# discount_rewards([10, 0, -50], 0.8) -> [-22, -40, -50]
```

```python
def training_step(batch_size):                            # Double DQN
    states, actions, rewards, next_states, dones, truncateds = sample_experiences(batch_size)
    next_Q_values = model.predict(next_states, verbose=0)
    best_next_actions = next_Q_values.argmax(axis=1)
    next_mask = tf.one_hot(best_next_actions, n_outputs).numpy()
    max_next_Q_values = (target.predict(next_states, verbose=0) * next_mask).sum(axis=1)
    runs = 1.0 - (dones | truncateds)
    target_Q_values = (rewards + runs * discount_factor * max_next_Q_values).reshape(-1, 1)
    mask = tf.one_hot(actions, n_outputs)
    with tf.GradientTape() as tape:
        all_Q_values = model(states)
        Q_values = tf.reduce_sum(all_Q_values * mask, axis=1, keepdims=True)
        loss = tf.reduce_mean(loss_fn(target_Q_values, Q_values))
    grads = tape.gradient(loss, model.trainable_variables)
    optimizer.apply_gradients(zip(grads, model.trainable_variables))

for episode in range(600):
    obs, info = env.reset()
    for step in range(200):
        epsilon = max(1 - episode / 500, 0.01)
        obs, reward, done, truncated, info = play_one_step(env, obs, epsilon)
        if done or truncated:
            break
    if episode > 50:
        training_step(batch_size)
    if episode % 50 == 0:
        target.set_weights(model.get_weights())
```

## Reference Tables
| Method | Learns | Needs model of env? | Policy type | Notes |
|---|---|---|---|---|
| Value / Q-value iteration | V*, Q* | Yes (T, R) | Greedy | Dynamic programming; fast on small MDPs |
| TD learning | V | No | – | Running average with α |
| Q-learning | Q* | No | Off-policy | Tabular; slow convergence |
| DQN (+ target, double, dueling, PER) | Q_θ | No | Off-policy | Scales to big state spaces |
| REINFORCE | π_θ | No | On-policy | Simple; high variance |
| Actor-critic (A2C/A3C, SAC, PPO) | π_θ + critic | No | On/off | Most practical modern choices |
| MCTS + nets (AlphaZero/MuZero) | π, V | Simulator / learned | Planning | Board games |

| Policy (CartPole, 500 episodes) | Mean reward |
|---|---|
| Hardcoded "push toward lean" | 41.7 (max 63) |
| REINFORCE NN (5 hidden units, 150 iterations × 10 episodes) | ≈ 200 (max) |
| DQN | Reaches 200 but erratic (catastrophic forgetting) |

## Worked Example
**Q-value iteration on the 3-state MDP** (s0: a0 → stay with +10 at 70%; a1 stay; a2 …; s1: a2 through fire (−50) to s2; s2: a1 back to s0 with +40 at 80%):
```python
Q_values = np.full((3, 3), -np.inf)
for state, actions in enumerate(possible_actions):
    Q_values[state, actions] = 0.0
gamma = 0.90
for iteration in range(50):
    Q_prev = Q_values.copy()
    for s in range(3):
        for a in possible_actions[s]:
            Q_values[s, a] = np.sum([transition_probabilities[s][a][sp]
                                     * (rewards[s][a][sp] + gamma * Q_prev[sp].max())
                                     for sp in range(3)])
# Q ≈ [[18.9, 17.0, 13.6], [0., -inf, -4.9], [-inf, 50.1, -inf]]
Q_values.argmax(axis=1)   # [0, 0, 1]: in s1 stay put (avoid the fire)
```
With γ = 0.95, the optimal action in s1 becomes a2 (go through the fire), since valuing the future more makes the pain worth it. Tabular Q-learning (random exploration, α₀ = 0.05 with power decay) converges to the same values, but takes ~8,000 iterations vs < 20 for Q-value iteration.

## Key Takeaways
1. Frame the problem as agent, environment, actions, rewards, γ; start from a hardcoded baseline policy.
2. Policy gradients: sample actions, compute discounted normalized advantages, weight the gradients; simple but sample-hungry.
3. Known small MDP: use (Q-)value iteration. Unknown: Q-learning with sufficient exploration (ε-greedy with decay).
4. DQN needs a replay buffer, a target network, double DQN, and optionally dueling + PER; plot rewards, not loss; save the best model.
5. For real projects prefer modern actor-critics (PPO, SAC) via libraries (TF-Agents, Stable-Baselines) and inject domain knowledge.
6. Expect instability and seed sensitivity; budget time accordingly.

## Connects To
- **Ch 4/11**: gradient descent, learning-rate schedules (power decay for α).
- **Ch 12**: GradientTape custom training loops.
- **Ch 14**: CNNs for Atari pixel observations.
- **Ch 19**: distributing training / many parallel environments.
