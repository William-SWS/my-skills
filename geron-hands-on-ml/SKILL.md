---
name: geron-hands-on-ml
description: "Knowledge base from \"Hands-On Machine Learning with Scikit-Learn, Keras, and TensorFlow\" (3rd ed.) by Aurélien Géron. Use when applying Géron's ML project checklist, Scikit-Learn pipelines, model evaluation, ensembles, deep learning training recipes (Keras/TensorFlow), CNNs, RNNs/transformers, generative models, RL, or deployment at scale; studying the book; or referencing its concepts."
---

<!-- argument-hint: [topic, framework name, or chapter number] -->

# Hands-On Machine Learning with Scikit-Learn, Keras, and TensorFlow (3rd ed.)
**Author**: Aurélien Géron | **Pages**: ~1,196 | **Chapters**: 19 + 4 appendices | **Generated**: 2026-10-18

## How to Use This Skill

- **Without arguments**: load the core frameworks below for reference.
- **With a topic**: ask about `precision/recall`, `transfer learning`, `DQN`, or another topic from the Topic Index; I read the relevant chapter file before answering.
- **With a chapter**: ask for `ch07`; I load that chapter file.
- **Browse**: ask "what chapters do you have?" to see the full index.

When you ask about a topic not covered in Core Frameworks below, I will read the relevant chapter file first.

---

## Core Frameworks & Mental Models

### 1. The ML project checklist (App A, Ch 2)
Use these 8 steps on every project: **frame → get data → explore → prepare → shortlist models → fine-tune → present → launch/monitor/maintain**.
- **Frame first**: the business objective, how the output is used downstream, the current solution's performance (your baseline), and the minimum acceptable performance. Classify the task (supervised? batch/online? instance/model-based?).
- **Split before you look**: a stratified, reproducible test set (stable ID hash or fixed seed). Never tweak after measuring test performance.
- **Write functions/pipelines for every transformation**, so preparation choices become tunable hyperparameters and the same code runs in production.

### 2. Bad data vs bad model (Ch 1, 4)
- *Bad data*: too little, nonrepresentative (sampling noise/bias: the Literary Digest poll), noisy, irrelevant features ("garbage in, garbage out").
- *Bad model*: **overfitting** (too complex for the amount/noisiness of data: simplify, regularize, add data, denoise) vs **underfitting** (bigger model, better features, less regularization).
- Diagnose with **learning curves**: high and close means underfit; a gap means overfit. Think in terms of the **bias/variance trade-off** (+ irreducible noise).
- Proxy training data → add a **train-dev set** to separate overfitting from **data mismatch**.
- **No Free Lunch**: evaluate a few reasonable models; no model is a priori best.

### 3. Scikit-Learn pipeline discipline (Ch 2)
- API: **estimators** `fit`, **transformers** `transform`, **predictors** `predict`; hyperparameters are public attributes, learned params end with `_`.
- Build a `ColumnTransformer` (impute → engineer ratios/log/RBF-cluster features → scale; one-hot categoricals with `handle_unknown="ignore"`) inside a full `Pipeline`, then tune preprocessing and model together (`step__sub__param`).
- **Fit scalers/imputers on training data only.** Custom transformers subclass `BaseEstimator, TransformerMixin`, have no `*args`, and `fit` returns `self`.
- Evaluate with k-fold CV (mean ± std); shortlist 3–5 models with *different errors*; prefer **randomized search** over grid search; ensemble; report the test score with a 95% CI.

### 4. Classification evaluation (Ch 3)
- Accuracy lies on skewed data (a dummy gets 90%). Use the **confusion matrix, precision = TP/(TP+FP), recall = TP/(TP+FN), F1**.
- A classifier is a **ranker plus a threshold**: get out-of-fold scores (`cross_val_predict(method="decision_function")`), choose the threshold on the PR curve for the business target. **"99% precision? At what recall?"**
- **PR curve when positives are rare or FPs matter more; ROC otherwise.**
- **Error analysis**: normalized, errors-only confusion matrix, fix the dominant confusion (data, features, augmentation).

### 5. Model-family heuristics (Ch 4–9)
- Linear models: closed form for small n; SGD/mini-batch for large n or out-of-core; **always some regularization** (Ridge default, Lasso for sparsity, Elastic Net when n > m or features are correlated); **scale features**.
- SVMs: small/medium nonlinear data; **try a linear kernel first, then RBF**; reduce C/γ when overfitting.
- Trees: no scaling needed, interpretable, but high variance and axis-aligned; regularize (`max_depth`, `min_samples_leaf`).
- **Ensembles** (diversity is everything): soft voting, bagging/RF/Extra-Trees (variance ↓), boosting (bias ↓; GBRT with low LR + early stopping; HistGB for large data with native categoricals/NaN), stacking with out-of-fold blending.
- Dimensionality reduction: try raw data first; `PCA(n_components=0.95)`; random projection for huge n; t-SNE for visualization.
- Unsupervised: k-means (scale first; choose k with silhouette diagrams), DBSCAN for arbitrary shapes, GMM (+BIC) for ellipsoids/density/anomalies; **cluster-then-label representatives + propagate** for semi-supervised learning.

### 6. Deep learning training recipe (Ch 10–11)
- Output layer and loss follow the task: regression (no activation, MSE/Huber), binary/multilabel (sigmoid + binary cross-entropy), multiclass (softmax + sparse categorical cross-entropy).
- **Default config (Table 11-3)**: He init; ReLU (shallow) / Swish (deep); BN if deep; early stopping (+ weight decay); **Nesterov SGD or AdamW**; **1cycle or performance scheduling**. For plain dense stacks: LeCun + SELU, no BN.
- **The learning rate is the #1 hyperparameter**: sweep it exponentially and pick ~10× below divergence; retune when the batch size changes.
- Prefer **more layers over more neurons**; "stretch pants" (oversize the net and regularize).
- Regularize with dropout (top 1–3 layers), max-norm, ℓ2 (not with Adam; use AdamW), data augmentation. **MC dropout** for uncertainty.
- **Reuse pretrained models**: freeze, train the head, unfreeze the top layers, recompile with a lower LR.
- Always: input normalization inside the model, `EarlyStopping(restore_best_weights=True)`, `ModelCheckpoint`, TensorBoard.

### 7. Architecture map (Ch 14–17)
- **CNNs**: 3×3 conv stacks, filters doubling as resolution halves, GAP head; ResNet skips, separable convs, SE blocks; pick pretrained models by accuracy/size/latency; detection = FCN/YOLO + NMS (mAP), segmentation = transposed convs + skips.
- **Sequences**: beat naive seasonal + SARIMA baselines; windows via `tf.data`; seq-to-seq for multi-step; LSTM/GRU, Conv1D, WaveNet for long context; layer norm and recurrent dropout.
- **NLP**: mask padding; subword tokenization; encoder–decoder + attention; **Transformers** (multi-head attention, positional encodings, padding and causal masks); fine-tune pretrained models (Hugging Face); audit for bias.
- **Generative**: autoencoders (undercomplete/denoising/sparse/VAE), GANs (two-phase loop, DCGAN rules, mode collapse), diffusion (predict the noise; latent diffusion).

### 8. Production & scale (Ch 13, 19)
- Put **preprocessing layers inside the exported model** to avoid training/serving skew.
- `tf.data`: interleave → parallel map → cache → shuffle → batch → **prefetch**.
- Export versioned **SavedModels**; serve with TF Serving (gRPC for heavy load, hot swaps, batching) or Vertex AI; TFLite + quantization for edge; TF.js for browser/privacy.
- Scale training with `tf.distribute` (MirroredStrategy → MultiWorkerMirrored); data parallelism first.
- **Monitor live performance and input quality; models rot, so automate retraining.**

### 9. Reinforcement learning (Ch 18)
- Policy gradients (REINFORCE: discounted, normalized advantages weight the gradients) vs value-based (Bellman, Q-value iteration, Q-learning, **DQN + replay buffer + target net + double/dueling + PER**). Track rewards, not loss. "RL must be forced to work": expect instability; inject domain knowledge.

---

## Chapter Index

| # | Title | Key Frameworks |
|---|-------|----------------|
| [ch01](chapters/ch01-ml-landscape.md) | The Machine Learning Landscape | T/E/P, 3 classification axes, bad data vs bad model, train-dev set |
| [ch02](chapters/ch02-end-to-end-project.md) | End-to-End ML Project | 8 steps, stratified split, ColumnTransformer, CV, randomized search |
| [ch03](chapters/ch03-classification.md) | Classification | Confusion matrix, P/R trade-off, PR vs ROC, OvR/OvO, error analysis |
| [ch04](chapters/ch04-training-models.md) | Training Models | Normal eq vs GD, learning curves, bias/variance, Ridge/Lasso/EN, logistic/softmax |
| [ch05](chapters/ch05-support-vector-machines.md) | Support Vector Machines | Large margin, C, kernel trick, RBF γ, SVR |
| [ch06](chapters/ch06-decision-trees.md) | Decision Trees | CART, Gini/entropy, regularization, axis sensitivity, high variance |
| [ch07](chapters/ch07-ensembles-random-forests.md) | Ensemble Learning & Random Forests | Voting, bagging/OOB, RF/Extra-Trees, AdaBoost, GBRT/HGB, stacking |
| [ch08](chapters/ch08-dimensionality-reduction.md) | Dimensionality Reduction | Curse of dimensionality, PCA 95%, random projection/JL, LLE, t-SNE |
| [ch09](chapters/ch09-unsupervised-learning.md) | Unsupervised Learning | k-means++/silhouette, label propagation, DBSCAN, GMM/BIC, anomaly detection |
| [ch10](chapters/ch10-neural-networks-keras.md) | Intro to ANNs with Keras | Perceptron→MLP, backprop, Sequential/Functional/Subclassing, callbacks, Keras Tuner |
| [ch11](chapters/ch11-training-deep-networks.md) | Training Deep Neural Networks | Init, activations, BN, transfer learning, optimizers, 1cycle, dropout/MC dropout |
| [ch12](chapters/ch12-custom-models-tensorflow.md) | Custom Models & Training with TF | Custom losses/metrics/layers, GradientTape, custom loops, TF Functions |
| [ch13](chapters/ch13-data-loading-preprocessing.md) | Loading & Preprocessing Data | tf.data pipeline, prefetch, TFRecord/protobuf, preprocessing layers, embeddings |
| [ch14](chapters/ch14-cnn-computer-vision.md) | Deep Computer Vision with CNNs | Conv/pooling, ResNet/Xception/SENet, pretrained transfer, YOLO, segmentation |
| [ch15](chapters/ch15-rnns-cnns-sequences.md) | Processing Sequences (RNNs & CNNs) | Baselines/SARIMA, windowing, seq2seq, LSTM/GRU, WaveNet |
| [ch16](chapters/ch16-nlp-rnns-attention.md) | NLP with RNNs and Attention | Char-RNN, masking, encoder–decoder, beam search, attention, Transformer, HF |
| [ch17](chapters/ch17-autoencoders-gans-diffusion.md) | Autoencoders, GANs & Diffusion | Stacked/denoising/sparse/VAE, GAN training, DCGAN, StyleGAN, DDPM |
| [ch18](chapters/ch18-reinforcement-learning.md) | Reinforcement Learning | Policy gradients, MDP/Bellman, Q-learning, DQN variants, PPO/SAC |
| [ch19](chapters/ch19-training-deploying-at-scale.md) | Training & Deploying at Scale | SavedModel, TF Serving, Vertex AI, TFLite, GPUs, distribution strategies |
| [ch20](chapters/ch20-appendix-a-ml-project-checklist.md) | App A: ML Project Checklist | Full 8-step checklist |
| [ch21](chapters/ch21-appendices-b-c-d-tf-internals.md) | App B–D: Autodiff, Data Structures, TF Graphs | Reverse-mode autodiff, ragged/sparse, concrete functions, AutoGraph |

## Topic Index

- **1cycle / LR schedules** → ch11
- **Activation functions (ReLU, ELU, SELU, GELU, Swish)** → ch10, ch11
- **AdaBoost / Gradient boosting / HistGB / XGBoost** → ch07
- **Adam / AdamW / Nesterov / RMSProp** → ch11
- **Anomaly & novelty detection** → ch09, ch17
- **ARIMA / SARIMA / naive forecasting** → ch15
- **Attention (Bahdanau, Luong, multi-head)** → ch16
- **Autodiff (forward/reverse mode)** → ch10, ch12, ch21
- **Autoencoders / VAE** → ch17
- **Batch normalization / layer normalization** → ch11, ch15
- **Beam search / sampling temperature** → ch16
- **BERT / GPT / T5 / Hugging Face** → ch16
- **Bias/variance trade-off / learning curves** → ch04
- **Callbacks / TensorBoard / early stopping** → ch04, ch10, ch11
- **CNN architectures (LeNet → EfficientNet)** → ch14
- **Clustering (k-means, DBSCAN, GMM)** → ch09
- **Confusion matrix / precision / recall / ROC / PR** → ch03
- **Cross-validation / Grid / Randomized search** → ch02, ch07
- **Custom layers / losses / metrics / training loops** → ch12
- **Data augmentation** → ch03, ch13, ch14
- **Decision trees / CART** → ch06
- **Diffusion models / Stable Diffusion** → ch17
- **Dimensionality reduction (PCA, LLE, t-SNE, random projection)** → ch08
- **Distribution strategies / GPUs / TPUs** → ch19
- **DQN / Q-learning / policy gradients / MDPs** → ch18
- **Dropout / MC dropout / max-norm / ℓ1-ℓ2** → ch11
- **Embeddings / TextVectorization / StringLookup** → ch13, ch16
- **Ensembles / voting / stacking / random forests** → ch07
- **Feature scaling / imputation / encoding** → ch02, ch13
- **GANs / DCGAN / StyleGAN / mode collapse** → ch17
- **Gradient descent (batch/SGD/mini-batch)** → ch04
- **Initialization (Glorot, He, LeCun)** → ch11
- **Keras APIs (Sequential, Functional, Subclassing)** → ch10, ch12
- **Keras Tuner / Vertex AI tuning** → ch10, ch19
- **LSTM / GRU / RNNs / WaveNet** → ch15, ch16
- **ML project checklist** → ch02, ch20
- **Multiclass / multilabel / multioutput** → ch03
- **Object detection / YOLO / segmentation** → ch14
- **Overfitting / underfitting / regularization** → ch01, ch04, ch11
- **Pipelines / ColumnTransformer / custom transformers** → ch02
- **Ragged / sparse tensors / TF graphs** → ch12, ch21
- **Semi-supervised / active learning / label propagation** → ch09
- **SVM / kernel trick** → ch05
- **tf.data / TFRecord / prefetch** → ch13
- **TF Serving / SavedModel / TFLite / TF.js / Vertex AI** → ch19
- **Transfer learning / pretrained models** → ch11, ch14, ch16
- **Transformers / positional encoding / ViT** → ch16

## Supporting Files

- [glossary.md](glossary.md): all key terms with definitions
- [patterns.md](patterns.md): all techniques and design patterns
- [cheatsheet.md](cheatsheet.md): decision rules, defaults, trade-offs

---

## Scope & Limits

This skill covers the book's content (3rd edition, 2022; TensorFlow 2.x / Keras 2 APIs such as `save_format="tf"` and `tf.keras.*`, Gym API with `truncated`). APIs have evolved since (e.g. Keras 3, Gymnasium), so check current library docs before copying code verbatim. For implementation in your codebase, combine with project-specific tools. Figures and formula images weren't extracted; equations are paraphrased from the text.
