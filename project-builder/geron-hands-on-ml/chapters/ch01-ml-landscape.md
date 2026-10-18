# Chapter 1: The Machine Learning Landscape

## Core Idea
ML means programming computers to learn from data instead of from hand-written rules. Classify an ML system along three independent axes (supervision, batch vs online, instance vs model-based), then diagnose failures as either **bad data** or **bad model**, and never trust a model you have not evaluated on held-out data.

## Frameworks Introduced
- **Mitchell's T/E/P definition**: "A program learns from experience E with respect to task T and performance measure P if its performance on T, measured by P, improves with E."
  - When to use: framing any new ML problem.
  - How: name T (e.g. flag spam), E (labeled emails), P (e.g. accuracy). If you can't name P, you can't evaluate the model.
- **When ML is the right tool** (4 cases): (1) existing solutions need lots of fine-tuning or long rule lists; (2) complex problems with no good traditional solution; (3) fluctuating environments (retrain on new data); (4) mining insights from complex problems and large data ("data mining").
- **Three classification axes** (not exclusive, combine freely):
  1. *Training supervision*: supervised, unsupervised, semi-supervised, self-supervised, reinforcement.
  2. *Batch vs online*: can it learn incrementally from a stream?
  3. *Instance-based vs model-based*: compare to stored examples, or fit parameters of a model?
- **Bad data vs bad model**: the two things that go wrong.
  - Bad data: insufficient quantity, nonrepresentative (sampling noise / sampling bias), poor quality (errors, outliers, noise), irrelevant features.
  - Bad model: overfitting, underfitting.
- **Holdout validation → train-dev set**: train set / validation (dev) set / test set; when training data differs from production data, add a **train-dev set** to separate overfitting from data mismatch.

## Key Concepts
- **Label / target**: the desired output; "label" for classification, "target" for regression.
- **Feature (predictor, attribute)**: an input variable.
- **Self-supervised learning**: generate labels from unlabeled data (e.g. mask part of an image, predict it), then usually fine-tune via **transfer learning**.
- **Online (incremental) learning**: train on instances/mini-batches sequentially; the **learning rate** sets the adapt-vs-forget trade-off.
- **Out-of-core learning**: online algorithms used offline for datasets too big for memory.
- **Model parameter vs hyperparameter**: parameters are learned; hyperparameters belong to the learning algorithm and are fixed before training (e.g. regularization strength).
- **Regularization**: constraining a model to reduce overfitting.
- **Utility/fitness function vs cost function**: measure of how good vs how bad a model is; linear regression minimizes a cost (distance between predictions and targets).
- **Inference**: applying a trained model to new cases.
- **No Free Lunch theorem** (Wolpert 1996): with zero assumptions about the data, no model is a priori better; you pick models by making reasonable assumptions and evaluating a few.

## Mental Models
- Think of the word **"model"** as three things: a model *type* (linear regression), a fully specified *architecture* (linear regression, 1 input, 1 output), and the *trained model* (with θ values). Model selection = choosing type + architecture; training = finding parameters.
- Think of **online learning risk** as "garbage in, live": bad data degrades a live system quickly. Monitor inputs and be able to switch learning off or roll back.
- Use the **train-dev diagnostic** when training data comes from a cheap proxy source: poor on train-dev means overfitting; good on train-dev but poor on dev means data mismatch, so make the training data look more like production data.
- **"The unreasonable effectiveness of data"** (Banko & Brill 2001; Norvig et al. 2009): with enough data, simple algorithms catch up with sophisticated ones. Small/medium datasets are still the norm, though, so algorithms still matter.

## Anti-patterns
- **Rule-list spam filters**: brittle, hard to maintain, and fooled when spammers adapt ("4U" becomes "For U").
- **Sampling bias even with huge samples**: the 1936 Literary Digest poll (2.4M answers) predicted Landon over Roosevelt, because the mailing lists skewed wealthy and only <25% responded (nonresponse bias).
- **Selecting models on the test set**: you overfit the test set and the generalization error looks optimistic. Use a validation set or cross-validation.
- **Too small or too large a validation set**: small means imprecise selection; large means too little training data. Prefer repeated cross-validation.

## Code Examples
```python
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression

data_root = "https://github.com/ageron/data/raw/main/"
lifesat = pd.read_csv(data_root + "lifesat/lifesat.csv")
X = lifesat[["GDP per capita (USD)"]].values
y = lifesat[["Life satisfaction"]].values

model = LinearRegression()          # swap for KNeighborsRegressor(n_neighbors=3)
model.fit(X, y)
X_new = [[37_655.2]]                # Cyprus' GDP per capita in 2020
print(model.predict(X_new))         # [[6.30165767]]
```
- **What it demonstrates**: the whole model-based workflow in 5 lines, and that switching to instance-based learning (k-NN) is a one-line change.

## Reference Tables
| Symptom | Diagnosis | Remedies |
|---|---|---|
| Great on train, poor on validation | Overfitting | Simpler model (fewer params/features), regularize, more data, reduce noise |
| Poor on train | Underfitting | More powerful model, better features, less regularization |
| Good on train-dev, poor on dev | Data mismatch | Preprocess training data to resemble production data |
| Poor everywhere, small data | Insufficient data | More data; simpler models |

| Task | Typical technique (chapter) |
|---|---|
| Image classification / segmentation | CNNs, transformers (14, 16) |
| Text classification, summarization | RNNs, CNNs, transformers (16) |
| Revenue forecasting | Linear/polynomial regression, SVM, RF, ANN (4–7, 10) |
| Fraud / anomaly detection | Isolation forest, GMM, autoencoders (9, 17) |
| Customer segmentation | k-means, DBSCAN (9) |
| Visualization | Dimensionality reduction, t-SNE (8) |
| Game bots | Reinforcement learning (18) |

## Worked Example
**Does money make people happy?** (model-based workflow)
1. *Study the data*: join OECD Better Life Index with World Bank GDP per capita (Turkey $28k → 5.5; Denmark $56k → 7.6). The scatterplot shows a noisy linear trend.
2. *Select a model*: `life_satisfaction = θ0 + θ1 × GDP_per_capita`.
3. *Train*: linear regression finds θ0 = 3.75, θ1 = 6.78 × 10⁻⁵.
4. *Infer*: Cyprus ($37,655) gives 3.75 + 37,655 × 6.78e-5 ≈ **6.30**.
5. *Instance-based alternative*: the 3 nearest countries by GDP (Israel 7.2, Lithuania 5.9, Slovenia 5.9) average **6.33**, very close.
6. *Caveat*: the sample covered only $23.5k–$62.5k. Adding poorer and richer countries changes the fitted line a lot, so the data was nonrepresentative. A high-degree polynomial would fit the full data perfectly but overfit. Regularizing (a smaller slope) generalizes better.

## Key Takeaways
1. Name T, E, and P before writing code.
2. Classify the system on the three axes; this drives the architecture (batch retraining vs online, etc.).
3. Most failures are data failures: get more, more representative, cleaner data with relevant features.
4. Overfitting = model too complex for the amount/noisiness of data; fix it with regularization, controlled by a hyperparameter.
5. Default split: 80/20 train/test, but hold out a smaller fraction for huge datasets (1% of 10M = 100k is plenty).
6. Tune hyperparameters on a validation set (or CV), retrain on train+val, then touch the test set **once**.
7. With proxy training data, add a train-dev set to tell overfitting apart from data mismatch.

## Connects To
- **Ch 2**: the full end-to-end project applying this workflow.
- **Ch 4**: regularization, learning curves, bias/variance formalized.
- **App A**: the ML project checklist.
- **No Free Lunch**: why every chapter compares several models.
