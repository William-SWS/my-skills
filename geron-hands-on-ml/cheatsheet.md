# Cheatsheet: Géron's Judgment Calls

## Decision rules
- **New project** → pull out the App A checklist; frame the business objective, current baseline and minimum acceptable performance first.
- **Before looking at data** → split off a stratified, reproducible test set, then explore only a copy of the training set.
- **Model great on train, bad on validation** → overfitting: simplify, regularize, add data, denoise. **Bad on both** → underfitting: bigger model, better features, less regularization.
- **Good on train-dev, bad on dev** → data mismatch: make training data look like production.
- **Skewed classes** → ignore accuracy; compare to `DummyClassifier`; use P/R/F1. **Rare positives or FP-costly** → PR curve; else ROC.
- **Someone says "99% precision"** → ask "at what recall?".
- **Hyperparameter space large** → `RandomizedSearchCV` (or Bayesian/Hyperband); grid only for tiny spaces. **Best value at the grid edge** → extend the range.
- **Changed batch size** → retune the learning rate.
- **SVM overfitting** → reduce C (and γ for RBF). **AdaBoost overfitting** → fewer estimators / stronger base regularization. **GBRT** → lower LR + more trees + early stopping + subsample.
- **Tabular data** → try RF / Extra-Trees / (Hist)GradientBoosting early; HGB handles NaN and categoricals natively.
- **Big NN from scratch?** → first look for a pretrained model on a similar task; freeze, train the head, unfreeze the top, lower the LR, recompile.
- **Adam generalizes poorly** → try Nesterov SGD. **Adam + weight decay** → AdamW, not ℓ2.
- **Dropout model looks fine** → evaluate training loss *without* dropout before declaring no overfitting.
- **Risk-sensitive predictions** → MC dropout (100 samples) for calibrated probabilities + std.
- **Forecasting** → beat naive seasonal (t − season) and SARIMA with rolling-origin evaluation before trusting any NN.
- **Text** → mask padding; prefer pretrained encoders / Hugging Face; audit for bias.
- **Deploying** → preprocessing inside the SavedModel; versioned folders; gRPC for heavy traffic; monitor inputs as well as outputs.

## Defaults & thresholds
| Item | Default |
|---|---|
| Train/test split | 80/20; ~1% when m ≈ 10M |
| CV folds | 3 (quick) – 10 (final) |
| PCA dims | `n_components=0.95` (tune for supervised) |
| Random forest | √n features per split, 500 trees |
| GBRT | lr 0.05, early stopping `n_iter_no_change=10` |
| Hidden layers / neurons | 1–5 / 10–100 (stretch pants + early stopping) |
| Initializer / activation | He + ReLU (Swish if deep); LeCun + SELU for self-normalizing MLPs |
| Optimizer | Adam η = 0.001 (β1 0.9, β2 0.999) or SGD momentum 0.9 + Nesterov |
| Batch size | largest that fits GPU (with warmup) or 2–32 if unstable |
| Dropout | 10–50% (RNN 20–30%, CNN 40–50%); top 1–3 layers |
| BN momentum | 0.9 / 0.99 / 0.999 (more 9s for big data, small batches) |
| Embedding size | 10–300 |
| One-hot vs embedding | < ~10–20 categories one-hot; > 50 embeddings |
| Gradient clipping | `clipnorm=1.0` (RNNs) |
| Discount γ (RL) | 0.9 (~10 steps) – 0.99 (~100 steps) |
| ε-greedy | 1.0 → 0.01 over ~500 episodes |
| Anomaly threshold | density percentile = acceptable defect rate (e.g. 2%) |

## Trade-off matrices
| Linear regression solver | Large m | Large n | Out-of-core |
|---|---|---|---|
| Normal eq / SVD | ✔ | ✘ | ✘ |
| Batch GD | ✘ | ✔ | ✘ |
| SGD / mini-batch | ✔ | ✔ | ✔ |

| Clusterer | Shapes | Needs k | Scales |
|---|---|---|---|
| k-means | spherical | yes | best |
| DBSCAN/HDBSCAN | any, even density | no | ok |
| GMM | ellipsoids | yes (BIC) | ok |

| Generative | Speed | Quality | Stability |
|---|---|---|---|
| VAE | fast | blurry | stable |
| GAN | fast | sharp | unstable |
| Diffusion | slow | sharp+diverse | stable |

## Decision tree: "my NN isn't training well"
- Loss diverges → lower η; check scaling; gradient clipping.
- Loss plateaus early → η too low or dying ReLUs → LR sweep; Leaky ReLU/Swish; He init; BN.
- Train ≪ val loss → regularize (dropout, weight decay, augmentation, early stopping) or get data.
- Both high → bigger/deeper net, better features, train longer.
- GPU idle → `tf.data` parallel map + `prefetch`; cache.
- OOM → smaller batch, strides, float16, `set_memory_growth`.

## Tells & smells
- Training RMSE = 0 → memorization (unregularized tree).
- ROC AUC 0.96 on rare positives → check the PR curve before celebrating.
- Normalized confusion column bright → model dumps doubt into that class.
- A tiny result improvement after many tries → "torturing the data until it confesses".
- DQN reward collapses after peaking → catastrophic forgetting; save the best weights.
- Forecast model crushed on recent data → regime shift; revalidate on recent periods.
