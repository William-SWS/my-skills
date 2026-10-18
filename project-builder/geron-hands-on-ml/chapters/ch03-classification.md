# Chapter 3: Classification

## Core Idea
Evaluating classifiers is harder than training them. Accuracy misleads on skewed data, so use the **confusion matrix, precision/recall, and PR/ROC curves**, pick the decision threshold that fits the business need, then use **error analysis** of the confusion matrix to decide what to improve. Covers binary, multiclass (OvR/OvO), multilabel and multioutput classification on MNIST.

## Frameworks Introduced
- **Always beat a dummy baseline**: `DummyClassifier` (most frequent class) reaches 90.9% accuracy on "5 vs not-5". The SGD classifier's 95% is barely better.
- **Precision/Recall trade-off via the decision threshold**:
  - When to use: always for binary classifiers in production.
  - How: get out-of-fold scores with `cross_val_predict(..., method="decision_function")` (or `predict_proba[:,1]`), compute `precision_recall_curve`, pick the lowest threshold that meets the target (`(precisions >= 0.90).argmax()`), then predict with `scores >= threshold`.
- **"At what recall?"**: when someone asks for 99% precision, ask "at what recall?".
- **PR curve vs ROC curve rule**: prefer the **PR curve when the positive class is rare or you care more about false positives than false negatives**; otherwise ROC. ROC AUC looks great (0.96) when positives are rare even for a mediocre classifier.
- **OvR vs OvO** for multiclass with binary learners: OvR trains N classifiers; OvO trains N×(N−1)/2 (45 for MNIST), each on a small subset, so it's preferred for algorithms that scale poorly with dataset size (SVMs). Scikit-Learn picks automatically; force it with `OneVsRestClassifier` / `OneVsOneClassifier`.
- **Error analysis via normalized confusion matrices**: `ConfusionMatrixDisplay.from_predictions(..., normalize="true", values_format=".0%")`, then zero the diagonal with `sample_weight=(y_pred != y)`. Normalize by row ("true") to see where each class goes; by column ("pred") to see what a predicted class really is.

## Key Concepts
- **Confusion matrix**: rows = actual class, columns = predicted. TN, FP / FN, TP.
- **Precision** = TP / (TP + FP): accuracy of positive predictions.
- **Recall (sensitivity, TPR)** = TP / (TP + FN): fraction of positives detected.
- **F1 score** = 2 / (1/P + 1/R), the harmonic mean. It favors similar P and R.
- **ROC curve**: TPR vs FPR (1 − specificity); AUC = 1 is perfect, 0.5 is random.
- **`cross_val_predict`**: "clean" out-of-fold predictions for each training instance.
- **Multilabel classification**: multiple binary labels per instance (`KNeighborsClassifier` supports it natively). Evaluate with `f1_score(average="macro")` or `"weighted"` (by support).
- **`ClassifierChain`**: chain per-label models, each using previous labels' predictions (true labels during training, with `cv=` for out-of-sample).
- **Multioutput-multiclass**: each label can be multiclass (e.g. denoising: one label per pixel, values 0–255).
- **Estimated probabilities ≠ calibrated probabilities**: use `sklearn.calibration`.

## Mental Models
- Think of a **binary classifier as a ranker plus a threshold**: the model produces a score ordering; the business picks the cut. Precision curves are bumpy because raising the threshold can remove a TP.
- Pick the threshold **just before precision falls off a cliff** on the PR curve (here ~80% recall), unless the project dictates otherwise.
- Use **high precision** when false positives are costly (kid-safe video filter: reject many good videos, keep only safe ones). Use **high recall** when misses are costly (shoplifter detection: tolerate false alarms).
- Think of the bright column in an errors-only confusion matrix as **"the class the model dumps doubt into"** (8 for MNIST). Fix that class first.
- **Linear models are sensitive to shifts/rotations**: 3 vs 5 confusions come from a small pixel difference. Center/deskew images or **augment with shifted/rotated copies**.

## Anti-patterns
- **Reporting accuracy on skewed classes**: the dummy classifier gets 90%.
- **Building curves from test-set predictions during development**: use out-of-fold predictions on the training set.
- **Comparing raw `predict()` outputs when you need thresholds**: use `decision_function` / `predict_proba`.
- **Treating `predict_proba` as calibrated**: an RF's 50–60% bucket was actually ~94% positive.
- **Forgetting scaling** for SGD: accuracy goes from 85.8% to 89.1% just with `StandardScaler`.
- **Not shuffling** before CV/SGD: folds miss classes and order-sensitive learners degrade.

## Code Examples
```python
from sklearn.model_selection import cross_val_predict
from sklearn.metrics import precision_recall_curve, precision_score, recall_score

y_scores = cross_val_predict(sgd_clf, X_train, y_train_5, cv=3,
                             method="decision_function")
precisions, recalls, thresholds = precision_recall_curve(y_train_5, y_scores)

idx_for_90_precision = (precisions >= 0.90).argmax()
threshold_for_90_precision = thresholds[idx_for_90_precision]   # ~3370
y_train_pred_90 = (y_scores >= threshold_for_90_precision)
precision_score(y_train_5, y_train_pred_90)  # 0.900
recall_score(y_train_5, y_train_pred_90)     # 0.480
```
- **What it demonstrates**: choosing an operating point on the PR curve without touching the test set.

```python
from sklearn.metrics import ConfusionMatrixDisplay
y_train_pred = cross_val_predict(sgd_clf, X_train_scaled, y_train, cv=3)
sample_weight = (y_train_pred != y_train)          # errors only
ConfusionMatrixDisplay.from_predictions(y_train, y_train_pred,
                                        sample_weight=sample_weight,
                                        normalize="true", values_format=".0%")
```

## Reference Tables
| Model (5-detector, train CV) | Precision | Recall | F1 | ROC AUC |
|---|---|---|---|---|
| DummyClassifier | – (no positives) | 0 | – | – |
| SGDClassifier (threshold 0) | 83.7% | 65.1% | 0.733 | 0.960 |
| SGD @ threshold 3370 | 90.0% | 48.0% | – | – |
| RandomForestClassifier (p ≥ 0.5) | 99.1% | 86.6% | 0.924 | 0.998 |

| Task type | Output | Example | Metric |
|---|---|---|---|
| Binary | 1 of 2 classes | 5 vs not-5 | P/R, F1, PR-AUC, ROC-AUC |
| Multiclass | 1 of N | digit 0–9 | accuracy, confusion matrix |
| Multilabel | several binary | large? odd? | macro/weighted F1 |
| Multioutput | several multiclass | denoised pixels | per-output metrics |

## Worked Example
**Error analysis on MNIST (SGD, scaled)**:
1. Plain confusion matrix: mostly diagonal; cell (5,5) looks darker, but is it fewer 5s or worse on 5s?
2. Normalize by row: only **82% of 5s** are correct; 10% of 5s go to 8, but only 2% of 8s go to 5. Confusion is asymmetric.
3. Errors only (`sample_weight`): the **column for 8 is bright**, so many classes are misclassified as 8. Row normalization by predicted class (`normalize="pred"`): 56% of misclassified 7s are actually 9s.
4. Action candidates: gather more "looks-like-8" data; add features (count closed loops: 8 has 2, 6 has 1, 5 has 0); preprocess (center, deskew).
5. Plotting 3s vs 5s in a 2×2 grid shows most errors are obvious to humans. SGD is a linear model assigning per-pixel weights, so it's sensitive to shifts: the junction position separates 3 vs 5. **Data augmentation** with shifted/rotated images fixes much of this.

## Key Takeaways
1. Compare every classifier to a `DummyClassifier`; use precision/recall/F1, not accuracy, on imbalanced data.
2. Always evaluate with out-of-fold predictions (`cross_val_predict`) and keep the test set untouched.
3. Choose the threshold from the PR curve to meet the business constraint. Precision is free to raise; recall pays for it.
4. PR curve for rare positives or FP-sensitive tasks; ROC otherwise.
5. Scale inputs even for "simple" linear classifiers.
6. Do error analysis on normalized, errors-only confusion matrices; then target the dominant confusion with data, features, or preprocessing.
7. Multilabel: KNN/RF handle it natively; `ClassifierChain` captures label dependencies.

## Connects To
- **Ch 2**: cross-validation, `cross_val_score`, stratification.
- **Ch 4**: logistic/softmax regression, the models behind `predict_proba`.
- **Ch 5**: SVC and why OvO suits SVMs.
- **Ch 7**: random forests' `predict_proba`.
- **Ch 14**: data augmentation for images.
