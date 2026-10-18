# Appendices B, C, D: Autodiff, Special Data Structures, TensorFlow Graphs

## Core Idea
These three appendices explain TensorFlow internals the main chapters rely on. **Autodiff** (App B): why TensorFlow uses **reverse-mode autodiff** to get every gradient in one backward pass. **Special data structures** (App C): strings, ragged, sparse, tensor arrays, sets, queues. **TF graphs** (App D): how TF Functions become polymorphic **concrete functions** via **tracing** and **AutoGraph**, and how they handle variables/resources.

## Frameworks Introduced
### Appendix B: Autodiff (example f(x, y) = x²y + y + 2; ∂f/∂x = 2xy = 24, ∂f/∂y = x² + 1 = 10 at (3, 4))
- **Manual differentiation**: apply calculus rules by hand. Exact, but tedious and error-prone for complex functions.
- **Finite difference approximation**: (f(x + ε) − f(x))/ε gives 24.00004 and 10.0000000003. Imprecise, and needs **n + 1 calls for n parameters** (impossible for millions). Still useful to **check** other implementations.
- **Forward-mode autodiff**: propagate derivatives from inputs to outputs, e.g. with **dual numbers** a + bε (ε² = 0): h(a + ε) = h(a) + h′(a)ε gives the value and derivative in one pass. Accurate, but **one pass per input**, so it's bad with many inputs and few outputs (NNs).
- **Reverse-mode autodiff** (TensorFlow): a forward pass computes node values, then a reverse pass applies the **chain rule** (∂f/∂x = ∂f/∂nᵢ × ∂nᵢ/∂x) from the output down. It gets **all partial derivatives in passes = number of outputs + 1**, regardless of the number of inputs, so it's ideal for one scalar loss and millions of parameters. It produces symbolic derivative graphs, so second derivatives are possible. Custom C++ ops must supply a gradient function.

| Technique | Passes for all gradients | Accuracy | Supports arbitrary code | Note |
|---|---|---|---|---|
| Numerical differentiation | n_inputs + 1 | Low | Yes | Trivial; good for testing |
| Symbolic differentiation | N/A | High | No | Builds a very different graph |
| Forward-mode autodiff | n_inputs | High | Yes | Uses dual numbers |
| Reverse-mode autodiff | n_outputs + 1 | High | Yes | TensorFlow's choice |

### Appendix C: Special data structures
- **Strings** (`tf.string`): atomic byte strings (Unicode is auto-encoded to UTF-8; the length isn't part of the shape). Unicode code-point tensors are int32. `tf.strings.length(unit="UTF8_CHAR")`, `unicode_encode`, `unicode_decode` (returns ragged).
- **Ragged tensors** (`tf.RaggedTensor`, `tf.ragged.constant`): lists of arrays of different lengths along ragged dimensions; `tf.concat` on axis 0 or 1; `.to_tensor()` pads with zeros. Recurrent Keras layers support them natively.
- **Sparse tensors** (`tf.SparseTensor(indices, values, dense_shape)`): indices must be in reading order (use `tf.sparse.reorder` otherwise); `tf.sparse.to_dense`, `sparse_dense_matmul`. Fewer ops are supported (you can multiply by a scalar but not add one).
- **Tensor arrays** (`tf.TensorArray`): lists of same-shape tensors for loops in dynamic models. **Always reassign** (`array = array.write(i, t)`) or it breaks in graph mode. `clear_after_read`, `dynamic_size=True` (slower), `.stack()`.
- **Sets** (`tf.sets`): integer/string sets as tensors on the last axis; `union`, `intersection`, `difference`, `size` return sparse tensors. Pad with a value and set `default_value` (empty string for string sets).
- **Queues** (`tf.queue`): `FIFOQueue`, `PaddingFIFOQueue`, `PriorityQueue` (int64 priority first; lower is dequeued first), `RandomShuffleQueue`. They block when full/empty; mostly superseded by `tf.data`.

### Appendix D: TensorFlow graphs
- **Polymorphism → concrete functions**: each new **input signature** (dtype + shape, or a new Python value) traces a new `ConcreteFunction` with its own optimized `FuncGraph` of **symbolic tensors**. `tf_cube.get_concrete_function(tf.constant(2.0))`.
- **Exploring graphs**: `concrete_function.graph.get_operations()` (Placeholder, Const, Pow, Identity); `op.inputs`/`op.outputs`; `get_operation_by_name`, `get_tensor_by_name("Identity:0")`; `function_def.signature`.
- **Tracing**: Python code (e.g. `print`) runs **only during tracing**, so side effects happen once per new signature. Python ints trigger a retrace per value.
- **`input_signature`**: `@tf.function(input_signature=[tf.TensorSpec([None, 28, 28], tf.float32)])` gives one concrete function for any batch size; mismatched inputs raise `ValueError`.
- **AutoGraph control flow**: `for i in range(10)` is **unrolled** (10 add ops; static); `for i in tf.range(10)` becomes a `While` op (dynamic, in the graph). Same idea for `if` with tensor conditions → `tf.cond`.
- **Resources (variables, datasets, queues)**: ops on them are stateful and executed in order. Variables can be arguments (`DT_RESOURCE`) or captured; prefer encapsulating them in classes (as Keras does). Use **`assign`/`assign_add`/`assign_sub`**, never Python `=`/`+=` on variables.
- **Keras and TF functions**: Keras auto-converts custom losses/layers/models. Disable with `dynamic=True` (layer/model) or `compile(..., run_eagerly=True)` for debugging.

## Mental Models
- **Reverse mode = "how much does the loss blame each node?"**: blame flows backward via the chain rule, and every parameter gets its share in a single sweep.
- **Tracing = recording a script with placeholders**: Python executes once to write the graph, then the graph runs many times.
- **Ragged > padded when lengths vary a lot**: no wasted compute or masks.

## Anti-patterns
- Using finite differences to train (use them only to verify gradients).
- Forgetting to reassign `TensorArray.write` results.
- Relying on Python side effects or `range()` loops inside TF functions.
- Calling TF functions with many distinct Python scalar values (graph explosion).
- `+=` on a `tf.Variable` inside a TF function.

## Code Examples
```python
def f(x, y):
    return x**2*y + y + 2

def derivative(f, x, y, x_eps, y_eps):
    return (f(x + x_eps, y + y_eps) - f(x, y)) / (x_eps + y_eps)

derivative(f, 3, 4, 0.00001, 0)   # 24.00004 (true: 24)

@tf.function(input_signature=[tf.TensorSpec([None, 28, 28], tf.float32)])
def shrink(images):
    return images[:, ::2, ::2]

@tf.function
def add_10(x):
    for i in tf.range(10):         # dynamic While op, not 10 unrolled adds
        x += 1
    return x

class Counter:
    def __init__(self):
        self.counter = tf.Variable(0)

    @tf.function
    def increment(self, c=1):
        return self.counter.assign_add(c)
```

## Key Takeaways
1. TensorFlow gets all gradients in one reverse pass (reverse-mode autodiff); finite differences are only for checking.
2. Use ragged tensors for variable-length data, sparse tensors for mostly-zero data, TensorArrays for loop accumulation.
3. Each new input signature traces a new concrete function; pin `input_signature` for predictable graphs.
4. In TF functions, use `tf.range`, tensor conditions, `tf.print`, and `assign*` on variables.
5. Use `run_eagerly=True` to debug Keras custom code.

## Connects To
- **Ch 10**: backpropagation = reverse-mode autodiff + GD.
- **Ch 12**: GradientTape, TF Function rules, special data structures.
- **Ch 13/16**: string, ragged and sparse tensors in text pipelines.
- **Ch 19**: SavedModel signatures are concrete functions.
