# Chapter 10: Introduction to Artificial Neural Networks with Keras

## Core Idea
ANNs went from McCulloch–Pitts neurons to **perceptrons** to **multilayer perceptrons (MLPs) trained by backpropagation** (reverse-mode autodiff + gradient descent) with nonlinear activations. Keras offers three ways to build them: the **Sequential API** (simple stacks), the **Functional API** (multi-input/output, Wide & Deep), and the **Subclassing API** (dynamic models). Train with `compile`/`fit`/`evaluate`/`predict`, add **callbacks** (checkpoints, early stopping, TensorBoard), and tune hyperparameters with **Keras Tuner**.

## Frameworks Introduced
- **Why ANNs now**: huge data, compute (GPUs, Moore's law, cloud), better training algorithms, local optima turned out to be benign, and a virtuous circle of funding.
- **Perceptron (TLU, Rosenblatt 1957)**: step function over wᵀx + b. **Hebb's rule** ("cells that fire together, wire together") gives the perceptron learning rule. Linear boundaries only, so it can't solve XOR (Minsky & Papert), but stacking layers can.
- **Backpropagation** (Rumelhart, Hinton, Williams 1985), per mini-batch:
  1. *Forward pass*: compute every layer's output and keep the intermediate results.
  2. Measure the loss.
  3. *Reverse pass*: chain rule from the output back to the inputs, giving the gradients for all weights.
  4. *Gradient descent step*.
  - Requires **random weight init** (to break symmetry) and **differentiable activations** (sigmoid, tanh, ReLU).
- **Why activations**: chaining linear layers is still linear; nonlinearity lets a deep enough net approximate any continuous function.
- **MLP architecture recipes** (Tables 10-1, 10-2): see Reference Tables.
- **Three Keras APIs**: Sequential (declarative, inspectable, easy to save and debug); Functional (arbitrary DAGs: Wide & Deep, multiple inputs, multiple/auxiliary outputs); Subclassing (imperative `call()` with loops, ifs, low-level TF ops; harder to inspect, clone and save).
- **Wide & Deep** (Cheng et al. 2016): concatenate inputs (wide path, simple rules) with the deep stack's output (complex patterns).
- **Hyperparameter search for NNs**: Keras Tuner `RandomSearch`, `Hyperband` (successive halving like `HalvingRandomSearchCV`), `BayesianOptimization` (Gaussian process; `alpha`, `beta`). Subclass `kt.HyperModel` to tune preprocessing or `fit()` args such as batch size.
- **Hyperparameter heuristics**:
  - *Hidden layers*: start with 1–2; deep nets are far more **parameter efficient** because they model hierarchical structure (low-level, then intermediate, then high-level features). This also enables transfer learning by reusing lower layers.
  - *Neurons*: same size in all hidden layers usually works as well as a pyramid. **"Stretch pants" approach**: pick a model bigger than needed and use early stopping / regularization so it doesn't overfit. Avoid bottleneck layers that are too small.
  - **"More bang for your buck by increasing the number of layers instead of the number of neurons per layer."**
  - *Learning rate*: the most important. The optimum is ~½ of the max (divergent) rate. Find it by training a few hundred iterations while increasing η exponentially (1e-5 to 10), plot loss vs η (log scale), and pick about 10× below the point where the loss shoots up.
  - *Batch size*: either use the largest that fits in GPU RAM (with learning-rate warmup), or stick to small batches (2–32), which often generalize better. Try large first and fall back if training is unstable or generalization is poor.
  - *Activation*: ReLU default for hidden layers. *Iterations*: don't tune them; use early stopping.
  - **When you change any hyperparameter, especially batch size, retune the learning rate.**

## Key Concepts
- **Dense (fully connected) layer**: h = ϕ(XW + b); W is [inputs × neurons], b is [neurons]; Keras calls W the **kernel**.
- **Feedforward NN (FNN)**; **deep NN (DNN)** = deep stack of hidden layers.
- **Reverse-mode autodiff**: efficient for many parameters with one scalar loss (App B).
- **Losses**: `sparse_categorical_crossentropy` (integer class labels), `categorical_crossentropy` (one-hot), `binary_crossentropy` (sigmoid / multilabel), `mse`, `huber` (quadratic below δ, linear above, so robust to outliers).
- **`Normalization` layer**: `adapt()` on training data; its stats are non-trainable weights.
- **`history.history`**: per-epoch loss/metrics, plotted as learning curves (training metrics are averaged during the epoch, so shift them half an epoch left when comparing).
- **`class_weight` / `sample_weight`** in `fit()` for skewed data.
- **Saving**: `model.save(path, save_format="tf")` (SavedModel: architecture, weights, optimizer state) / `tf.keras.models.load_model`; `save_weights`/`load_weights`. Subclassed models save weights, but their Python code must be present.
- **Callbacks**: `ModelCheckpoint(save_best_only=True)`, `EarlyStopping(patience=10, restore_best_weights=True)`, `TensorBoard(log_dir, profile_batch=(100, 200))`, custom `Callback` subclasses with `on_epoch_end`, etc.
- **TensorBoard**: SCALARS, GRAPHS, PROJECTOR, PROFILE, HPARAMS; `tf.summary` for scalars, histograms, images, audio, text.

## Mental Models
- Think of deep nets as **drawing a forest with copy-paste**: lower layers learn reusable parts (line segments), higher layers compose them (trees, then forests). That's why depth beats width and why transfer learning works.
- **Stretch pants**: oversize the network and let early stopping / regularization fit it to the data.
- **Auxiliary output as regularizer**: forces the lower part of the network to learn something useful on its own (loss weight 0.1 vs 0.9 for the main output).
- **Multitask learning**: one net with an output per task often beats separate nets, because shared features help all tasks.
- **Validation better than training early on?** An artifact: training loss is averaged over the epoch while validation is measured at its end.

## Anti-patterns
- **Zero-initializing weights**: all neurons stay identical.
- **`optimizer="sgd"` without setting `learning_rate`**: the default 0.01 is rarely right.
- **Wrong loss/label pairing** (one-hot labels with sparse loss, or the opposite); forgetting `Flatten` → shape errors.
- **Tweaking hyperparameters on the test set**.
- **Bottleneck layers that are too small**: lost information can't be recovered by later layers.
- **Profiling TensorBoard on the first batches**: let the net warm up (batches 100–200).

## Code Examples
```python
tf.random.set_seed(42)
model = tf.keras.Sequential([
    tf.keras.layers.Flatten(input_shape=[28, 28]),
    tf.keras.layers.Dense(300, activation="relu"),
    tf.keras.layers.Dense(100, activation="relu"),
    tf.keras.layers.Dense(10, activation="softmax")])
model.compile(loss="sparse_categorical_crossentropy",
              optimizer=tf.keras.optimizers.SGD(learning_rate=0.01),
              metrics=["accuracy"])
checkpoint_cb = tf.keras.callbacks.ModelCheckpoint("my_checkpoints", save_best_only=True)
early_stopping_cb = tf.keras.callbacks.EarlyStopping(patience=10, restore_best_weights=True)
history = model.fit(X_train, y_train, epochs=100, validation_data=(X_valid, y_valid),
                    callbacks=[checkpoint_cb, early_stopping_cb])
model.evaluate(X_test, y_test)          # ~88.6% on Fashion MNIST after 30 epochs
```

```python
input_wide = tf.keras.layers.Input(shape=[5])     # features 0–4
input_deep = tf.keras.layers.Input(shape=[6])     # features 2–7
norm_layer_wide = tf.keras.layers.Normalization()
norm_layer_deep = tf.keras.layers.Normalization()
norm_wide = norm_layer_wide(input_wide)
norm_deep = norm_layer_deep(input_deep)
hidden1 = tf.keras.layers.Dense(30, activation="relu")(norm_deep)
hidden2 = tf.keras.layers.Dense(30, activation="relu")(hidden1)
concat = tf.keras.layers.concatenate([norm_wide, hidden2])
output = tf.keras.layers.Dense(1)(concat)
aux_output = tf.keras.layers.Dense(1)(hidden2)
model = tf.keras.Model(inputs=[input_wide, input_deep], outputs=[output, aux_output])
model.compile(loss=("mse", "mse"), loss_weights=(0.9, 0.1),
              optimizer=tf.keras.optimizers.Adam(learning_rate=1e-3),
              metrics=["RootMeanSquaredError"])
norm_layer_wide.adapt(X_train_wide); norm_layer_deep.adapt(X_train_deep)
model.fit((X_train_wide, X_train_deep), (y_train, y_train), epochs=20,
          validation_data=((X_valid_wide, X_valid_deep), (y_valid, y_valid)))
```
- **What it demonstrates**: a functional-API Wide & Deep model with two inputs and an auxiliary regularizing output.

```python
import keras_tuner as kt
def build_model(hp):
    n_hidden = hp.Int("n_hidden", min_value=0, max_value=8, default=2)
    n_neurons = hp.Int("n_neurons", min_value=16, max_value=256)
    learning_rate = hp.Float("learning_rate", min_value=1e-4, max_value=1e-2, sampling="log")
    optimizer = hp.Choice("optimizer", values=["sgd", "adam"])
    ...
hyperband_tuner = kt.Hyperband(MyClassificationHyperModel(), objective="val_accuracy",
                               max_epochs=10, factor=3, hyperband_iterations=2, seed=42)
```

## Reference Tables
| Regression MLP | Typical value |
|---|---|
| # hidden layers | 1 to 5 |
| # neurons per hidden layer | 10 to 100 |
| # output neurons | 1 per prediction dimension |
| Hidden activation | ReLU |
| Output activation | None; ReLU/softplus if positive; sigmoid/tanh if bounded |
| Loss | MSE, or Huber if outliers |

| Classification MLP | Binary | Multilabel binary | Multiclass |
|---|---|---|---|
| # output neurons | 1 | 1 per label | 1 per class |
| Output activation | Sigmoid | Sigmoid | Softmax |
| Loss | X-entropy | X-entropy | X-entropy |

| Keras API | Use when | Trade-off |
|---|---|---|
| Sequential | Single stack of layers | Simplest; inspectable |
| Functional | Multi-input/output, skip connections, Wide & Deep | Static graph; still inspectable/saveable |
| Subclassing | Dynamic behavior (loops, conditionals) | Hidden architecture; harder to debug/save |

## Worked Example
**Fashion MNIST MLP**: 55,000 train / 5,000 valid / 10,000 test 28×28 images, scaled /255. Model: Flatten → Dense(300, ReLU) → Dense(100, ReLU) → Dense(10, softmax), 266,610 params (the first Dense has 784×300 + 300 = 235,500). SGD, 30 epochs, 1,719 batches/epoch (batch 32): train acc 92.0%, **val 88.9%**, test 88.6%; the gap shows slight overfitting. `predict(X_test[:3])` gives probabilities, then `argmax` gives [Ankle boot, Pullover, Trouser], all correct. Keras Tuner RandomSearch (5 trials) found 5 hidden layers × 70 neurons, Adam lr ≈ 4.1e-4 → val acc 87.4%.

## Key Takeaways
1. MLP = Dense layers with ReLU hidden activations; output activation and loss follow from the task (tables above).
2. Start with the Sequential API; switch to Functional for nontrivial topologies; Subclassing only when you need dynamism.
3. Always put normalization in the model (`Normalization` + `adapt`).
4. Use `EarlyStopping(restore_best_weights=True)` + `ModelCheckpoint` + TensorBoard on every run.
5. The learning rate is the #1 hyperparameter: find it with the exponential sweep and retune it when the batch size changes.
6. Prefer more layers over more neurons; oversize the net and regularize ("stretch pants").
7. Use Keras Tuner (Hyperband / Bayesian) for systematic search; log trials to TensorBoard's HPARAMS.

## Connects To
- **Ch 4**: GD, mini-batches, softmax/cross entropy, early stopping.
- **Ch 11**: initialization, better activations, batch norm, optimizers, LR schedules, regularization.
- **Ch 12**: custom losses, layers, models and training loops.
- **Ch 13**: `tf.data` and preprocessing layers.
- **App B**: reverse-mode autodiff.
