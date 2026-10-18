# Chapter 12: Custom Models and Training with TensorFlow

## Core Idea
When Keras's built-ins aren't enough, drop to TensorFlow's lower-level API: **tensors, operations, variables**. You can customize every Keras component (losses, metrics, activations, initializers, regularizers, constraints, layers, models), compute gradients with **`tf.GradientTape`**, write **custom training loops**, and speed up and port code via **TF Functions** (`@tf.function`: AutoGraph + tracing → optimized graphs). About 95% of the time Keras is enough; this chapter covers the other 5%.

## Frameworks Introduced
- **TensorFlow stack**: C++ ops with device-specific **kernels** (CPU/GPU/TPU), the execution engine, the low-level Python API, then the high-level Keras and `tf.data`. Ecosystem: TensorBoard, TFX, TF Hub, TF Serving, TFLite, TF.js, Model Garden.
- **Customization ladder** (pick the simplest that works):
  1. A plain function (loss `f(y_true, y_pred)`; activation `f(z)`; initializer `f(shape, dtype)`; regularizer `f(weights)`; constraint `f(weights)`).
  2. A factory function for hyperparameters (not saved with the model).
  3. A **subclass** with `get_config()` so hyperparameters are saved: `tf.keras.losses.Loss` (implement `call`), `Regularizer`/`Initializer`/`Constraint` (implement `__call__`), `Metric` (`update_state`/`result`), `Layer` (`build`/`call`), `Model`.
- **Streaming metrics**: metrics like precision **cannot be averaged across batches**. Subclass `tf.keras.metrics.Metric`, create state with `add_weight`, and implement `update_state()` and `result()` (`reset_states()` resets to 0).
- **Custom layer contract**: `__init__(..., **kwargs)` → `super().__init__(**kwargs)`; `build(batch_input_shape)` creates weights via `add_weight`; `call(X, training=False)`; `get_config()`. For dynamic shapes, `compute_output_shape()`. Multi-input: `call` takes a tuple; multi-output: returns a list (functional/subclassing only).
- **Losses/metrics from model internals**: call `self.add_loss(...)` and `self.add_metric(...)` inside `call()` (e.g. an auxiliary reconstruction loss).
- **Custom training loop recipe**: sample batch → `with tf.GradientTape():` forward with `training=True`, `loss = mean(main) + sum(model.losses)` → `tape.gradient(loss, model.trainable_variables)` → `optimizer.apply_gradients(zip(...))` → apply constraints → update metrics → reset at epoch end. **"Unless you're learning or you really need the extra flexibility, you should prefer using the fit() method"**, especially in a team.
- **TF Functions**: `tf.function(f)` or `@tf.function`. **AutoGraph** rewrites Python control flow into TF ops (`tf.while_loop`, `tf.cond`); **tracing** runs the function with symbolic tensors to build the graph. One graph is cached per unique input signature (shape + dtype) and per Python value. Optional XLA via `jit_compile=True`.

## Key Concepts
- **`tf.Tensor`**: immutable, NumPy-like; `tf.reduce_sum/mean/max`, `tf.transpose` (copies, unlike `.T`), `@` for matmul.
- **No implicit type conversion**: float32 + int32 raises; use `tf.cast`. **NumPy defaults to float64, TF to float32**, so set `dtype=tf.float32`.
- **`tf.Variable`**: mutable; `assign`, `assign_add`, `scatter_nd_update`. Item assignment isn't allowed. Usually created via `add_weight` and updated by optimizers.
- **Special structures**: `tf.SparseTensor`, `tf.TensorArray`, `tf.RaggedTensor`, string tensors (byte strings; `tf.strings`), sets (`tf.sets`), queues (FIFO, Priority, RandomShuffle, PaddingFIFO).
- **Loss reduction**: default `"AUTO"`/`SUM_OVER_BATCH_SIZE` (sum of weighted instance losses / batch size, which isn't the weighted mean). Return per-instance losses, not the mean, so sample/class weights work.
- **Saving custom objects**: `load_model(path, custom_objects={"HuberLoss": HuberLoss})`, or decorate with `@keras.utils.register_keras_serializable()`.
- **`GradientTape`**: records ops on variables; one reverse pass for all variables. `persistent=True` for multiple `gradient()` calls (then `del tape`); `tape.watch(tensor)` for non-variables; `tf.stop_gradient`; `tape.stop_recording()`. Gradient of a non-watched tensor is `None`.
- **Numerical stability**: sqrt at ~0 gives an inf gradient (add 1e-6); naive softplus overflows, so use `log(1 + exp(−|z|)) + max(0, z)`; `@tf.custom_gradient` supplies stable gradients.
- **`model.losses`**: regularization and `add_loss` terms (already reduced to scalars).

## Mental Models
- Think of **`build()` as lazy weight creation**: shapes are unknown until the first call, which is why layers can be shape-agnostic.
- Treat **metrics as accumulators, losses as per-batch differentiable signals**. Losses need useful gradients; metrics need interpretability.
- **TF Function = "trace once per signature"**: Python side effects (prints, counters, NumPy random) happen **only at trace time**. Keep the inputs of a TF function as tensors; reserve Python values for few-valued hyperparameters, or you'll generate many graphs.
- **Layer vs Model**: model components (reusable blocks) should be Layers; the trained object should be a Model (`fit`, `evaluate`, `save`).

## Anti-patterns
- **Returning the mean loss** from a custom loss: breaks sample/class weights.
- **Using NumPy / Python stdlib ops inside TF functions**: they run only during tracing and become constants.
- **Python `for i in range(x)` in a TF function**: unrolled at trace time; use `tf.range` (AutoGraph captures loops only over tensors/datasets).
- **Creating variables on every call** inside a TF function: create them on the first call only, or outside.
- **Forgetting `training=True`** in custom loops (BN/Dropout misbehave), or forgetting to apply weight constraints after `apply_gradients`.
- **Calling `tape.gradient` twice** on a non-persistent tape: RuntimeError.
- **Writing a custom loop when `fit()` would do**.

## Code Examples
```python
class HuberLoss(tf.keras.losses.Loss):
    def __init__(self, threshold=1.0, **kwargs):
        self.threshold = threshold
        super().__init__(**kwargs)

    def call(self, y_true, y_pred):
        error = y_true - y_pred
        is_small_error = tf.abs(error) < self.threshold
        squared_loss = tf.square(error) / 2
        linear_loss = self.threshold * tf.abs(error) - self.threshold ** 2 / 2
        return tf.where(is_small_error, squared_loss, linear_loss)

    def get_config(self):
        base_config = super().get_config()
        return {**base_config, "threshold": self.threshold}

class MyDense(tf.keras.layers.Layer):
    def __init__(self, units, activation=None, **kwargs):
        super().__init__(**kwargs)
        self.units = units
        self.activation = tf.keras.activations.get(activation)

    def build(self, batch_input_shape):
        self.kernel = self.add_weight(name="kernel",
                                      shape=[batch_input_shape[-1], self.units],
                                      initializer="glorot_normal")
        self.bias = self.add_weight(name="bias", shape=[self.units], initializer="zeros")

    def call(self, X):
        return self.activation(X @ self.kernel + self.bias)

    def get_config(self):
        base_config = super().get_config()
        return {**base_config, "units": self.units,
                "activation": tf.keras.activations.serialize(self.activation)}
```

```python
for epoch in range(1, n_epochs + 1):
    for step in range(1, n_steps + 1):
        X_batch, y_batch = random_batch(X_train_scaled, y_train)
        with tf.GradientTape() as tape:
            y_pred = model(X_batch, training=True)
            main_loss = tf.reduce_mean(loss_fn(y_batch, y_pred))
            loss = tf.add_n([main_loss] + model.losses)
        gradients = tape.gradient(loss, model.trainable_variables)
        optimizer.apply_gradients(zip(gradients, model.trainable_variables))
        for variable in model.variables:
            if variable.constraint is not None:
                variable.assign(variable.constraint(variable))
        mean_loss(loss)
        for metric in metrics:
            metric(y_batch, y_pred)
    for metric in [mean_loss] + metrics:
        metric.reset_states()
```
- **What it demonstrates**: a savable custom loss, a custom stateful layer, and the full custom loop with regularization losses and constraints.

## Reference Tables
| Component | Function form | Subclass | Method to implement |
|---|---|---|---|
| Loss | `f(y_true, y_pred)` | `keras.losses.Loss` | `call`, `get_config` |
| Activation | `f(z)` | `keras.layers.Layer` | `call` |
| Initializer | `f(shape, dtype)` | `keras.initializers.Initializer` | `__call__`, `get_config` |
| Regularizer | `f(weights)` | `keras.regularizers.Regularizer` | `__call__`, `get_config` |
| Constraint | `f(weights)` | `keras.constraints.Constraint` | `__call__`, `get_config` |
| Metric (streaming) | `f(y_true, y_pred)` (averaged) | `keras.metrics.Metric` | `update_state`, `result`, `get_config` |
| Layer | `keras.layers.Lambda` | `keras.layers.Layer` | `build`, `call`, `get_config` |
| Model | – | `keras.Model` | `call` (+ `get_config` to save) |

| TF Function rule | Do instead |
|---|---|
| NumPy / Python calls run only at trace | Use `tf.*` ops; `tf.py_function` as last resort (slow, not portable) |
| Side effects (logging) only at trace | `tf.print`, or move outside |
| Varying Python args make many graphs | Pass tensors; Python args only for hyperparams |
| Variables must be created on first call | Create outside, or in `build()` |
| Loops captured only over tensors/datasets | `for i in tf.range(n)` |
| Source must be available | Don't define in a shell / ship only .pyc |

## Worked Example
**Autodiff vs finite differences** for f(w1, w2) = 3w1² + 2w1w2 at (5, 3): analytically ∂f/∂w1 = 6w1 + 2w2 = **36**, ∂f/∂w2 = 2w1 = **10**. Finite differences with ε = 1e-6 give 36.000003 / 10.000000003: approximate, and they need one call per parameter (infeasible with millions). `tf.GradientTape` gives exactly [36.0, 10.0] in one reverse pass. With `tf.stop_gradient(2*w1*w2)` it gives [30.0, None]. For constants it gives [None, None] unless you call `tape.watch()`.

## Key Takeaways
1. Prefer built-ins, then functions, then subclasses with `get_config()` for anything with hyperparameters you need saved.
2. Implement streaming metrics for non-decomposable metrics (precision, recall).
3. Custom layers create weights in `build()`, honor `training`, and pass `**kwargs` up.
4. Use `add_loss`/`add_metric` for internal-state losses (reconstruction, activity penalties).
5. Write custom loops only when needed (multiple optimizers, GANs), and remember `training=True`, `model.losses`, constraints, and metric resets.
6. Keras auto-wraps your custom code in TF functions; follow the TF Function rules to stay fast and portable.
7. Guard numerics: epsilon in sqrt/log, stable softplus, `@tf.custom_gradient`.

## Connects To
- **Ch 10**: subclassing API, callbacks, saving.
- **Ch 11**: MCDropout layer, 1cycle callback, max-norm constraint.
- **Ch 13**: `tf.data` replaces `random_batch`.
- **Ch 17**: GAN custom training.
- **App B**: autodiff. **App C**: special data structures. **App D**: TF graphs and AutoGraph details.
