# Chapter 11: Training Deep Neural Networks

## Core Idea
Deep nets face four problems: **unstable (vanishing/exploding) gradients**, **too little labeled data**, **slow training**, and **overfitting**. The toolkit: good **initialization** (Glorot/He/LeCun), better **activations** (ReLU family, ELU/SELU, GELU/Swish/Mish), **batch normalization**, **gradient clipping**, **transfer learning / pretraining**, **faster optimizers** (momentum, NAG, RMSProp, Adam family), **learning rate schedules** (1cycle, performance), and **regularization** (ℓ1/ℓ2, dropout, MC dropout, max-norm). It ends with default configurations (Tables 11-3, 11-4).

## Frameworks Introduced
- **Glorot & Bengio insight**: keep output variance equal to input variance in both directions, so initialize by **fan-in/fan-out**. The old sigmoid + N(0,1) init saturated layers.
- **Initialization by activation** (Table 11-1): Glorot (σ² = 1/fan_avg) for none/tanh/sigmoid/softmax; **He** (2/fan_in) for ReLU/Leaky/ELU/GELU/Swish/Mish; **LeCun** (1/fan_in) for SELU. Keras defaults to Glorot uniform; set `kernel_initializer="he_normal"`.
- **Activation function choice** (author's tip): **ReLU is a good default for simple tasks** (fast, well-optimized). For more complex tasks Swish is a better default, GELU or Mish may be slightly better still, and Leaky ReLU (or parametrized) helps when runtime latency matters.
- **Dying ReLUs**: neurons stuck outputting 0. Fix with **Leaky ReLU** (α = 0.2 better than 0.01), **RReLU** (random α, regularizes), **PReLU** (learned α, overfit risk on small data).
- **SELU self-normalization**: conditions are standardized inputs, LeCun normal init, plain sequential MLP, and no ℓ1/ℓ2/max-norm/BN/regular dropout (use alpha dropout). It got little traction.
- **Batch Normalization (Ioffe & Szegedy 2015)**: per mini-batch, zero-center and normalize, then scale (γ) and shift (β). At test time it uses **moving averages** (μ, σ, non-trainable). It reduces vanishing gradients, allows larger learning rates, is less init-sensitive, and acts as a regularizer. Epochs are slower but convergence is faster.
- **Transfer learning procedure**:
  1. Reuse lower layers of a model trained on a similar task (same input size/type).
  2. Replace the output layer (and possibly top hidden layers).
  3. **Freeze** reused layers, train the new head a few epochs.
  4. **Unfreeze** top 1–2 layers (more with more data), recompile, and **lower the learning rate**.
  5. Rule: the more similar the tasks, the more layers you reuse.
- **"Torturing the data until it confesses"**: the author's 93.85% transfer result was cherry-picked across seeds/configs. Be suspicious of overly positive results.
- **Unsupervised pretraining**: with abundant unlabeled data, train an autoencoder/GAN (or greedy layer-wise RBMs historically), reuse the lower layers, and fine-tune on labeled data.
- **Pretraining on an auxiliary task / self-supervised learning**: e.g. face-pair "same person?" classifier, or masked-word prediction on text.
- **Optimizer progression**: SGD → **Momentum** (m ← βm − η∇; β = 0.9; terminal velocity 10× the gradient) → **Nesterov** (gradient at θ + βm; almost always faster) → **AdaGrad** (per-dimension decay; stops too early on DNNs) → **RMSProp** (decaying average; ρ = 0.9) → **Adam** (momentum + RMSProp + bias correction; β1 = 0.9, β2 = 0.999, η = 0.001) → **AdaMax**, **Nadam** (Adam + Nesterov), **AdamW** (decoupled weight decay).
- **Adaptive-optimizer caveat** (Wilson et al. 2017): they can generalize poorly on some datasets. **If disappointed, try NAG**.
- **LR schedules**: power (η₀/(1 + t/s)^c), exponential (η₀·0.1^(t/s)), piecewise constant, **performance** (`ReduceLROnPlateau`), **1cycle** (Smith 2018: ramp η linearly up to η_max for half of training, back down, then drop by orders of magnitude in the last epochs; momentum inversely 0.95 → 0.85 → 0.95).
- **Dropout (Hinton 2012)**: drop each neuron with probability p (10–50%; 20–30% RNNs, 40–50% CNNs) during training only; Keras scales the kept inputs by 1/(1 − p). Each step trains one of 2^N sub-networks, so the result is an implicit ensemble.
- **MC Dropout (Gal & Ghahramani 2016)**: at inference, average 100 stochastic forward passes with `training=True`. That gives better-calibrated probabilities plus uncertainty (std), without retraining.

## Key Concepts
- **Vanishing gradients**: gradients shrink going down layers, so lower layers barely update. **Exploding**: they grow (common in RNNs).
- **Saturation**: sigmoid derivative ≈ 0 at large |z|; sigmoid mean 0.5 (tanh, with mean 0, is better).
- **ELU**: negative outputs (mean near 0), nonzero gradient for z < 0, smooth if α = 1; slower to compute.
- **GELU** z·Φ(z); **Swish/SiLU** z·σ(βz); **Mish** z·tanh(softplus(z)). Smooth and nonmonotonic.
- **BN `momentum`** (0.9/0.99/0.999; more 9s for larger datasets and smaller batches); `axis` (normalize per feature, or per channel for CNNs).
- **Gradient clipping**: `clipvalue=1.0` (per component, may change direction) vs `clipnorm=1.0` (preserves direction). Used for RNNs where BN is tricky.
- **Weight decay ≠ ℓ2 with Adam**: use AdamW, not ℓ2, with adaptive optimizers.
- **Max-norm**: constrain ‖w‖₂ ≤ r per neuron (`kernel_constraint=max_norm(1.)`). It also helps with unstable gradients.
- **Sparse models**: strong ℓ1 regularization, or the TF Model Optimization Toolkit pruning API.
- **Folding BN**: merge BN into the previous layer's weights after training to cut latency.

## Mental Models
- Think of **momentum as a bowling ball** (velocity accumulates) and **Nesterov as looking ahead before stepping**. Friction (β < 1) damps oscillations.
- Think of **AdaGrad/RMSProp as per-parameter learning rates** that shrink faster along steep dimensions, pointing more directly at the optimum in elongated bowls.
- **Dropout = a workforce of interchangeable employees**: neurons can't co-adapt, so each must be useful on its own and less sensitive to its inputs.
- **Dropout hides overfitting in the loss curves**: evaluate training loss without dropout before comparing it to validation loss.
- **"With four parameters I can fit an elephant"** (von Neumann): with millions, you fit the zoo, so always regularize.
- **MC dropout for risk-sensitive apps**: a confident 84.4% can become 72.3% ± 0.18, which you'd treat with great caution.

## Anti-patterns
- **Training a very large DNN from scratch** without looking for a pretrained model on a similar task.
- **Forgetting to recompile** after freezing/unfreezing layers.
- **`clone_model` without `set_weights`**: random weights. Without cloning, training `model_B_on_A` also changes `model_A` (shared layers).
- **High learning rate when unfreezing**: wrecks pretrained weights.
- **SELU with skip connections/RNNs/BN/regular dropout**: breaks self-normalization.
- **Forcing `training=True` on models with BN for MC dropout**: subclass `MCDropout` instead.
- **ℓ2 + Adam**: use AdamW.

## Code Examples
```python
dense = tf.keras.layers.Dense(50, activation="relu", kernel_initializer="he_normal")

model = tf.keras.Sequential([          # BN before activation variant
    tf.keras.layers.Flatten(input_shape=[28, 28]),
    tf.keras.layers.Dense(300, kernel_initializer="he_normal", use_bias=False),
    tf.keras.layers.BatchNormalization(),
    tf.keras.layers.Activation("relu"),
    tf.keras.layers.Dense(100, kernel_initializer="he_normal", use_bias=False),
    tf.keras.layers.BatchNormalization(),
    tf.keras.layers.Activation("relu"),
    tf.keras.layers.Dense(10, activation="softmax")])

model_A = tf.keras.models.load_model("my_model_A")
model_A_clone = tf.keras.models.clone_model(model_A)
model_A_clone.set_weights(model_A.get_weights())
model_B_on_A = tf.keras.Sequential(model_A_clone.layers[:-1])
model_B_on_A.add(tf.keras.layers.Dense(1, activation="sigmoid"))
for layer in model_B_on_A.layers[:-1]:
    layer.trainable = False
model_B_on_A.compile(loss="binary_crossentropy",
                     optimizer=tf.keras.optimizers.SGD(learning_rate=0.001),
                     metrics=["accuracy"])
model_B_on_A.fit(X_train_B, y_train_B, epochs=4, validation_data=(X_valid_B, y_valid_B))
for layer in model_B_on_A.layers[:-1]:
    layer.trainable = True
model_B_on_A.compile(...)            # must recompile; keep LR low
model_B_on_A.fit(X_train_B, y_train_B, epochs=16, validation_data=(X_valid_B, y_valid_B))
```

```python
class MCDropout(tf.keras.layers.Dropout):
    def call(self, inputs, training=False):
        return super().call(inputs, training=True)

y_probas = np.stack([model(X_test, training=True) for sample in range(100)])
y_proba = y_probas.mean(axis=0)
y_std = y_probas.std(axis=0)

lr_scheduler = tf.keras.callbacks.ReduceLROnPlateau(factor=0.5, patience=5)
optimizer = tf.keras.optimizers.SGD(learning_rate=0.001, momentum=0.9, nesterov=True)
RegularizedDense = partial(tf.keras.layers.Dense, activation="relu",
                           kernel_initializer="he_normal",
                           kernel_regularizer=tf.keras.regularizers.l2(0.01))
```

## Reference Tables
**Table 11-3: Default DNN configuration**
| Hyperparameter | Default |
|---|---|
| Kernel initializer | He initialization |
| Activation | ReLU if shallow; Swish if deep |
| Normalization | None if shallow; batch norm if deep |
| Regularization | Early stopping; weight decay if needed |
| Optimizer | Nesterov accelerated gradients or AdamW |
| LR schedule | Performance scheduling or 1cycle |

**Table 11-4: Self-normalizing net (plain dense stack)**
| Hyperparameter | Default |
|---|---|
| Initializer | LeCun |
| Activation | SELU |
| Normalization | None (self-normalization) |
| Regularization | Alpha dropout if needed |
| Optimizer | Nesterov accelerated gradients |
| LR schedule | Performance scheduling or 1cycle |

**Table 11-2: Optimizers** (* bad, *** good)
| Class | Speed | Quality |
|---|---|---|
| SGD | * | *** |
| SGD(momentum) / Nesterov | ** | *** |
| Adagrad | *** | * (stops too early) |
| RMSprop / Adam / AdaMax / Nadam / AdamW | *** | ** or *** |

## Worked Example
**MC dropout on Fashion MNIST** (dropout model, rate 0.2): `model.predict(X_test[:1])` gives 84.4% ankle boot, 13.2% sneaker, 2.4% sandal. With 100 MC samples it's **72.3%** boot, 20.9% sneaker, 6.7% sandal; the std for class 9 is **0.183**. The probability mass moves to other footwear classes, which makes sense. Accuracy rises slightly, 87.0% → 87.2%. The lesson: for a medical/financial system, treat this prediction as highly uncertain, not as "84% confident". More samples mean better estimates and proportionally slower inference.

## Key Takeaways
1. Start from Table 11-3: He init + ReLU/Swish + BN (if deep) + early stopping + NAG/AdamW + 1cycle/performance scheduling.
2. Always normalize inputs; reuse pretrained models whenever a similar task exists.
3. Freeze, train the head, unfreeze the top layers with a low LR; recompile at each change.
4. Adam (η = 0.001) is easy; if generalization disappoints, try Nesterov SGD.
5. Find η with the exponential LR sweep; use 1cycle to train faster.
6. Regularize: dropout on the top 1–3 layers (rate 10–50%), max-norm, ℓ2 (not with Adam), early stopping.
7. Use MC dropout for better probabilities and uncertainty in risk-sensitive settings.
8. For low latency: fewer layers, ReLU/Leaky ReLU, fold BN; for sparsity: ℓ1 or TF-MOT pruning.

## Connects To
- **Ch 4**: GD, ℓ1/ℓ2, early stopping, learning rate.
- **Ch 10**: the LR sweep and Keras basics.
- **Ch 12**: custom callbacks (1cycle), custom layers (MCDropout), constraints.
- **Ch 14**: pretrained CNNs for transfer learning.
- **Ch 15**: gradient clipping and layer norm for RNNs.
- **Ch 17**: autoencoders for unsupervised pretraining.
