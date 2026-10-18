# Patterns & Techniques: Hands-On Machine Learning

## Reproducible Stratified Split
**When to use**: the first action on any dataset, before exploring.
**How**: `train_test_split(df, test_size=0.2, stratify=df["key_cat"], random_state=42)`, with `key_cat = pd.cut(important_feature, bins)`; or hash a stable ID (`crc32(id) < ratio * 2**32`) for growing datasets.
**Trade-offs**: stratifying on the wrong feature buys nothing; hash splits require stable, unique IDs.

## Full Preprocessing Pipeline (ColumnTransformer)
**When to use**: tabular data headed for production (Ch 2).
**How**: per-column pipelines (impute → ratio/log/RBF features → scale; most_frequent → OneHotEncoder(handle_unknown="ignore")) inside `ColumnTransformer`, wrapped with the model in a `Pipeline`; tune preprocessing params via `step__sub__param`.
**Trade-offs**: custom transformers must follow the fit/transform contract and be importable at load time.

## Shortlist → Randomized Search → Ensemble → Test Once
**When to use**: model selection (Ch 2, App A).
**How**: k-fold CV (mean ± std) on many default models; keep 3–5 with diverse errors; `RandomizedSearchCV`/Bayesian optimization; voting/stacking; a single test evaluation with a 95% CI.
**Trade-offs**: CV cost scales with k × combos; use `Halving*SearchCV` or Hyperband to save compute.

## Threshold Selection on the PR Curve
**When to use**: binary classifiers with business precision/recall targets (Ch 3).
**How**: `cross_val_predict(method="decision_function")` → `precision_recall_curve` → lowest threshold meeting the target → `scores >= threshold`.
**Trade-offs**: thresholds drift with data; recalibrate periodically.

## Error Analysis via Normalized Confusion Matrix
**When to use**: after a first decent classifier (Ch 3).
**How**: `ConfusionMatrixDisplay.from_predictions(normalize="true", sample_weight=(y_pred != y))`; inspect the brightest row/column; fix with data, features, or augmentation.
**Trade-offs**: manual and qualitative, but high-leverage.

## Learning-Curve Diagnosis
**When to use**: deciding between more data, more capacity, or regularization (Ch 4).
**How**: `learning_curve(...)`. High and close curves mean underfitting (bigger model/features); a gap means overfitting (more data/regularize).
**Trade-offs**: expensive for large models; use epoch curves instead.

## Semi-Supervised Label Propagation
**When to use**: lots of unlabeled data, few labels (Ch 9).
**How**: k-means into k clusters → label the instance nearest each centroid → propagate to the cluster → drop the farthest ~1% → train; iterate with active learning (uncertainty sampling).
**Trade-offs**: propagation errors at cluster boundaries; k must exceed the number of classes.

## Gradient Boosting with Shrinkage + Early Stopping
**When to use**: strong tabular baselines (Ch 7).
**How**: `GradientBoostingRegressor(learning_rate=0.05, n_estimators=500, n_iter_no_change=10, subsample=0.8)`, or `HistGradientBoosting*` (native categoricals/NaN) / XGBoost / LightGBM.
**Trade-offs**: sequential (no parallel trees); sensitive to the learning-rate × trees balance.

## Learning-Rate Range Test
**When to use**: before training any neural net (Ch 10–11).
**How**: grow η exponentially from 1e-5 to 10 over a few hundred iterations; plot loss vs log η; pick ~10× below the blow-up point. Retune when the batch size changes.
**Trade-offs**: noisy on small batches; combine with 1cycle or performance scheduling.

## Default Deep Net Recipe
**When to use**: a new dense/CNN model (Ch 11, Table 11-3).
**How**: He init; ReLU (shallow) / Swish (deep); BN if deep; Nesterov SGD or AdamW; 1cycle / ReduceLROnPlateau; EarlyStopping(restore_best_weights) + ModelCheckpoint; dropout on the top layers.
**Trade-offs**: BN adds per-epoch cost and complicates RNNs (use layer norm there).

## Transfer Learning (Freeze → Train Head → Unfreeze Top → Low LR)
**When to use**: images/text with limited labels (Ch 11, 14, 16).
**How**: `base(include_top=False)` + GAP + new head; freeze each base layer; train a few epochs at a high LR; unfreeze the top blocks; **recompile** with ~10× lower LR; continue.
**Trade-offs**: the input size/preprocessing must match the base (`preprocess_input`); domain gaps reduce gains.

## Preprocessing Inside the Model
**When to use**: any deployed model (Ch 13, 19).
**How**: Keras `Normalization`/`StringLookup`/`TextVectorization`/`Resizing` layers; `adapt()` on a training sample; for speed, preprocess once with the layers, train the core model, then wrap: `Sequential([prep_layers, model])`.
**Trade-offs**: some preprocessing can't be expressed as TF ops; on-the-fly preprocessing slows training.

## Efficient tf.data Pipeline
**When to use**: data larger than RAM or I/O-bound training (Ch 13).
**How**: `list_files` → `interleave(TextLineDataset/TFRecordDataset, num_parallel_calls)` → `map(parse, AUTOTUNE)` → `cache()` (if small) → `shuffle(big buffer)` → `batch` → `prefetch(1)`.
**Trade-offs**: shuffle buffers use RAM; true shuffling needs pre-shuffled sources.

## Time-Series Forecasting Ladder
**When to use**: any forecasting task (Ch 15).
**How**: naive seasonal baseline → SARIMA (rolling-origin eval) → linear on windows → RNN(32) + Dense → multivariate with known-future covariates → seq-to-seq (`return_sequences=True`, Dense(horizon)) → GRU/Conv1D/WaveNet for long context; MC dropout for error bars.
**Trade-offs**: regime shifts (Covid) break all learned patterns, so monitor recency.

## Encoder–Decoder with Attention / Transformer
**When to use**: seq-to-seq (translation, summarization) (Ch 16).
**How**: teacher forcing (SOS-shifted targets), bidirectional encoder, Attention or MultiHeadAttention with padding + causal masks, positional encodings; beam search at inference. In practice, fine-tune a pretrained Hugging Face model.
**Trade-offs**: attention is O(n²) in sequence length; training from scratch needs lots of data.

## VAE / GAN / Diffusion Generation
**When to use**: synthetic data, image generation (Ch 17).
**How**: VAE (μ, log σ², reparameterize, KL latent loss); DCGAN (two-phase loop, strided/transposed convs, BN, tanh output, LeakyReLU D); DDPM (cosine schedule, predict the noise, U-Net + time encoding).
**Trade-offs**: VAEs are blurry; GANs unstable (mode collapse); diffusion slow to sample (latent diffusion helps).

## Deep Q-Learning with Stabilizers
**When to use**: discrete-action RL (Ch 18).
**How**: ε-greedy (decay 1 → 0.01), replay buffer, target network synced periodically, Double DQN (online selects, target evaluates), optionally Dueling + PER; track episode rewards and save the best weights.
**Trade-offs**: catastrophic forgetting, seed sensitivity; PPO/SAC are often more practical.

## Serve & Scale
**When to use**: production (Ch 19).
**How**: versioned SavedModel folders → TF Serving (gRPC for heavy load, batching, warmup) or Vertex AI endpoints (autoscale; delete when idle); TFLite + quantization for edge; `MirroredStrategy`/`MultiWorkerMirroredStrategy` scope for multi-GPU training.
**Trade-offs**: distribution speedups are sublinear (bandwidth); cloud costs need hygiene.
