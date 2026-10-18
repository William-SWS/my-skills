# Chapter 13: Loading and Preprocessing Data with TensorFlow

## Core Idea
Deep learning datasets often don't fit in RAM. **`tf.data`** builds efficient streaming input pipelines (read, interleave, map, shuffle, batch, prefetch) that keep the GPU busy. **TFRecord + protobufs** store large data efficiently. **Keras preprocessing layers** embed preprocessing in the model itself, eliminating **training/serving skew**. TFDS and TF Hub provide ready datasets and pretrained components.

## Frameworks Introduced
- **Canonical input pipeline**: `list_files` (shuffled) → `interleave` (read N files in parallel, `skip(1)` headers) → `map(preprocess, num_parallel_calls)` → `shuffle(buffer)` → `batch` → `prefetch(1)`.
  - Shuffle well: shuffle the source files (e.g. `shuf`), read files interleaved, and use a large buffer (shuffling only works well if the buffer is large relative to the dataset).
  - `cache()` small datasets **after load/preprocess and before shuffle/repeat/batch/prefetch**, so each instance is preprocessed once and still reshuffled every epoch.
- **Prefetching**: CPU prepares batch n+1 while the GPU trains on n. With multithreaded load/parse, the GPU can approach 100% utilization. GPU memory **bandwidth** matters as much as compute and RAM.
- **"If it ain't broke, don't fix it"**: use TFRecords only when loading/parsing is the bottleneck.
- **Three places to preprocess**:
  1. Ahead of time (NumPy/Pandas/Scikit-Learn): fast training, but you must replicate it in production (skew risk).
  2. On the fly in `tf.data.map()`: same replication issue.
  3. **Preprocessing layers inside the model**: no skew. For speed, run the layers once on the data before training, train the core model, then wrap: `final_model = Sequential([norm_layer, model])` ("best of both worlds").
- **Categorical encoding decision**: few categories (< a dozen or two) → one-hot (`CategoryEncoding`, `StringLookup(output_mode="one_hot")`); many categories (> 50) → **embeddings**; 10–50 → experiment. Rare/unknown categories → OOV buckets (`num_oov_indices`); no adapt possible / out-of-core → `Hashing` (collisions).
- **Embeddings as learned representations**: 10–300 dims (tune). Similar categories end up close (representation learning); pretrained word embeddings transfer (with **biases**, e.g. "Man:Doctor :: Woman:Nurse", so fairness matters).
- **Text → numbers**: `TextVectorization` (standardize: lowercase and strip punctuation; split on whitespace; vocab sorted by frequency, 0 = padding, 1 = OOV); output ids (then Embedding), `multi_hot`, `count`, or **`tf_idf`** (weight log(1 + d/(f + 1))). For subwords use TF Text; for pretrained sentence encoders, TF Hub (`hub.KerasLayer`).

## Key Concepts
- **`tf.data.Dataset`**: streaming (not indexable); `from_tensor_slices`, `repeat`, `batch(drop_remainder=)`, `map`, `filter`, `take`, `shuffle(buffer_size, seed, reshuffle_each_iteration)`. Methods return **new** datasets.
- **`tf.data.AUTOTUNE`**: let TF pick parallelism.
- **`tf.io.decode_csv(line, record_defaults)`**: parses CSV fields; an empty-tensor default makes a field required.
- **TFRecord**: sequence of length + CRC + data + CRC records; `TFRecordWriter`, `TFRecordDataset(num_parallel_reads=)`, optional GZIP compression.
- **Protocol buffers**: `Example` = `Features` = map name → `Feature` (BytesList | FloatList | Int64List). Parse with `tf.io.parse_single_example` / `parse_example` (batched) and a description dict (`FixedLenFeature`, `VarLenFeature` → sparse). **`SequenceExample`** (context + FeatureLists) handles lists of lists (→ ragged tensors).
- **Images in TFRecords**: `tf.io.encode_jpeg` into BytesList; `tf.io.decode_image` back; `tf.io.serialize_tensor` for arbitrary tensors.
- **Preprocessing layers**: `Normalization` (adapt on a few hundred samples is enough), `Discretization` (bin_boundaries or num_bins + adapt), `CategoryEncoding` (one/multi-hot, count), `StringLookup`/`IntegerLookup`, `Hashing`, `Embedding`, `TextVectorization`, image `Resizing`/`Rescaling`/`CenterCrop`, augmentation `RandomFlip/Rotation/Zoom/Crop/Translation/Contrast` (training only).
- **One-hot + bias-free linear Dense = Embedding**, but Embedding avoids multiplications by zero.
- **TFDS**: `tfds.load(name, split=["train[:90%]", "train[90%:]", "test"], as_supervised=True)`.
- **`steps_per_execution`** in `compile()`: several batches per TF-function call, which speeds things up.

## Mental Models
- Think of the **input pipeline as an assembly line**: every stage parallel (interleave, map), with a buffer at the end (prefetch) so the expensive machine (GPU) never waits.
- **Preprocessing inside the model = deploying one artifact**: what you test is what you serve (web, mobile, TF.js) without reimplementing preprocessing in each language.
- **Hash collisions are the price of not adapting**; more buckets means fewer collisions but more parameters.
- **Multi-hot loses which feature a category came from**: offset ids per feature when encoding several features together.

## Anti-patterns
- **Forgetting to reassign** `dataset = dataset.map(...)`: nothing happens.
- **Small shuffle buffers on huge sorted data**: poor IID, so training suffers.
- **Feeding raw category ids to a NN**: their values aren't comparable; encode them.
- **Using an untrained Embedding as standalone preprocessing**: it's random until trained (unless pretrained).
- **Adapting `StringLookup` on a subset with one OOV bucket**: rare categories become indistinguishable.
- **Preprocessing in Pandas for training and in Java for serving**: skew.

## Code Examples
```python
X_mean, X_std = [...]          # from a StandardScaler on a sample
n_inputs = 8

def parse_csv_line(line):
    defs = [0.] * n_inputs + [tf.constant([], dtype=tf.float32)]
    fields = tf.io.decode_csv(line, record_defaults=defs)
    return tf.stack(fields[:-1]), tf.stack(fields[-1:])

def preprocess(line):
    x, y = parse_csv_line(line)
    return (x - X_mean) / X_std, y

def csv_reader_dataset(filepaths, n_readers=5, n_read_threads=None,
                       n_parse_threads=5, shuffle_buffer_size=10_000, seed=42,
                       batch_size=32):
    dataset = tf.data.Dataset.list_files(filepaths, seed=seed)
    dataset = dataset.interleave(
        lambda filepath: tf.data.TextLineDataset(filepath).skip(1),
        cycle_length=n_readers, num_parallel_calls=n_read_threads)
    dataset = dataset.map(preprocess, num_parallel_calls=n_parse_threads)
    dataset = dataset.shuffle(shuffle_buffer_size, seed=seed)
    return dataset.batch(batch_size).prefetch(1)

train_set = csv_reader_dataset(train_filepaths)
model.fit(train_set, validation_data=csv_reader_dataset(valid_filepaths), epochs=5)
```

```python
str_lookup_layer = tf.keras.layers.StringLookup()
str_lookup_layer.adapt(ocean_prox)
lookup_and_embed = tf.keras.Sequential([
    str_lookup_layer,
    tf.keras.layers.Embedding(input_dim=str_lookup_layer.vocabulary_size(), output_dim=2)])
num_input = tf.keras.layers.Input(shape=[8], name="num")
cat_input = tf.keras.layers.Input(shape=[], dtype=tf.string, name="cat")
encoded_inputs = tf.keras.layers.concatenate([num_input, lookup_and_embed(cat_input)])
outputs = tf.keras.layers.Dense(1)(encoded_inputs)
model = tf.keras.models.Model(inputs=[num_input, cat_input], outputs=[outputs])
```
- **What it demonstrates**: a production-grade CSV pipeline and a mixed numeric + learned-categorical-embedding model.

## Reference Tables
| Need | Layer / tool |
|---|---|
| Standardize numeric | `Normalization` + `adapt` |
| Bucketize numeric | `Discretization(bin_boundaries=...)` or `num_bins` + `adapt` |
| One/multi-hot ints | `CategoryEncoding(num_tokens, output_mode)` |
| Strings → ids/one-hot | `StringLookup(num_oov_indices, output_mode)` |
| No-adapt categorical | `Hashing(num_bins)` |
| High-cardinality categorical | `StringLookup` → `Embedding` |
| Text | `TextVectorization(output_mode="int"/"multi_hot"/"count"/"tf_idf")` |
| Pretrained text encoder | `hub.KerasLayer(url)` |
| Images | `Resizing`, `Rescaling(scale=1/255)`, `CenterCrop`, `Random*` augmentation |

| Dataset op | Position in pipeline |
|---|---|
| `list_files`, `interleave` | First (I/O) |
| `map(preprocess)` | Parallel, after reading |
| `cache()` | After preprocessing, before shuffle |
| `shuffle(buffer)` | Before batch |
| `batch()` | Before prefetch |
| `prefetch(1)` | Always last |

## Worked Example
**TF-IDF by hand**: training sentences ["To be", "!(to be)", "That's the question", "Be, be, be."], so d = 4. "be" appears in f = 3 sentences, giving weight log(1 + 4/(3 + 1)) = log 2 ≈ 0.693. In "Question: be or be?" it occurs twice, giving 2 × 0.693 = **1.386**; "question" (f = 1) gets log(1 + 4/2) = log 3 ≈ **1.099**; the OOV token ("or") gets ≈ 0.967. So frequent words are down-weighted and rare informative words count more.

## Key Takeaways
1. Use `tf.data` for anything beyond toy data: interleave files, parallel map, shuffle, batch, `prefetch(1)`.
2. Cache small preprocessed datasets; shuffle sources plus a large buffer for big ones.
3. Switch to TFRecords only if I/O/parsing is the bottleneck; use `Example`/`SequenceExample` protobufs.
4. Put preprocessing layers inside the deployed model to avoid training/serving skew; precompute during training for speed and wrap at the end.
5. One-hot for few categories, embeddings for many; OOV buckets or hashing for unseen values.
6. Prefer TF-IDF over raw counts for bag-of-words; use TF Hub / TF Text for stronger text features.

## Connects To
- **Ch 2**: Scikit-Learn pipelines and the same encodings (one-hot, scaling).
- **Ch 12**: TF Function rules apply to `map()` functions.
- **Ch 14**: image preprocessing and augmentation; `tf.data` with TFDS images.
- **Ch 16**: TextVectorization, embeddings, subword tokenization.
- **Ch 19**: serving models that include preprocessing.
