# Chapter 6: Decision Trees

## Core Idea
Decision trees are versatile, interpretable **white-box** models for classification, regression and multioutput tasks. They need almost no data preparation (no scaling). Scikit-Learn grows them greedily with **CART**. Their weaknesses are **overfitting** (they're nonparametric, so you must regularize), **orthogonal/axis-aligned boundaries**, and **high variance**. Ensembles (Ch 7) fix the variance.

## Frameworks Introduced
- **CART (Classification and Regression Tree)**: split on a single feature k and threshold tₖ minimizing the weighted impurity J(k, tₖ) = (m_left/m)G_left + (m_right/m)G_right; recurse until `max_depth` or no split reduces impurity.
  - Binary splits only (ID3 can have more children).
  - **Greedy**: finding the optimal tree is NP-complete (O(exp(m))), so settle for "reasonably good".
  - Regression: same algorithm, minimizing MSE instead of impurity; the leaf predicts the mean target.
- **Gini vs entropy**: "most of the time it does not make a big difference". Gini (default) is slightly faster; Gini isolates the most frequent class in its own branch, entropy gives slightly more balanced trees.
- **Regularization hyperparameters** (rule: **increasing `min_*` or reducing `max_*` regularizes**): `max_depth`, `max_features`, `max_leaf_nodes`, `min_samples_split`, `min_samples_leaf`, `min_weight_fraction_leaf`.
- **Parametric vs nonparametric**: trees' parameter count isn't fixed before training, so they adapt closely to data and overfit unless constrained. Linear models are parametric and risk underfitting.
- **Fix axis sensitivity with PCA rotation**: `make_pipeline(StandardScaler(), PCA())` before the tree reduces correlation between features and often simplifies the boundaries.

## Key Concepts
- **Gini impurity**: Gᵢ = 1 − Σₖ pᵢ,ₖ². A node is pure (G = 0) when all its instances belong to one class.
- **Entropy**: Hᵢ = −Σ pᵢ,ₖ log₂(pᵢ,ₖ) (over pᵢ,ₖ ≠ 0).
- **Node attributes**: `samples` (instances it applies to), `value` (per-class counts), `gini`.
- **Class probability**: ratio of class k in the leaf, identical everywhere in that leaf's region.
- **Prediction complexity**: O(log₂ m), independent of n, so predictions are very fast.
- **Training complexity**: O(n × m log₂ m).
- **Pruning**: alternative to pre-regularization; delete nodes whose purity gain isn't statistically significant (χ² test, p > 0.05).
- **White box vs black box**: trees explain their decisions (e.g. "petal length > 2.45 and width < 1.75"); random forests and NNs generally don't.
- **`tree_` attribute**: the full structure, for programmatic inspection; `export_graphviz` + Graphviz for visualization.

## Mental Models
- Think of a tree as **20-questions on features**: each node asks one yes/no threshold question; the leaf is the answer.
- **Staircase boundaries**: trees cut perpendicular to axes. A diagonal boundary needs many steps, and rotating the data 45° makes a simple boundary convoluted.
- **High variance = unstable**: Scikit-Learn picks features randomly at each node (`max_features`), so retraining on the same data can yield a very different tree. Average many trees to stabilize (random forest).
- Use trees when **interpretability matters** (auditable decisions, fairness reviews); use ensembles when **accuracy matters**.

## Anti-patterns
- **Default (unregularized) trees**: they memorize the training set (train RMSE 0 in Ch 2).
- **Trusting leaf probabilities far from training data**: a 6 cm long, 1.5 cm wide petal gets the same probability as 5 cm/1.5 cm.
- **Using trees on rotated/diagonal structure without PCA**.
- **Expecting one tree to be stable** across reruns or slight data changes.

## Code Examples
```python
from sklearn.datasets import load_iris, make_moons
from sklearn.tree import DecisionTreeClassifier, DecisionTreeRegressor, export_graphviz

iris = load_iris(as_frame=True)
X_iris = iris.data[["petal length (cm)", "petal width (cm)"]].values
tree_clf = DecisionTreeClassifier(max_depth=2, random_state=42).fit(X_iris, iris.target)
tree_clf.predict_proba([[5, 1.5]]).round(3)     # [[0., 0.907, 0.093]]

X_moons, y_moons = make_moons(n_samples=150, noise=0.2, random_state=42)
tree_clf1 = DecisionTreeClassifier(random_state=42).fit(X_moons, y_moons)
tree_clf2 = DecisionTreeClassifier(min_samples_leaf=5, random_state=42).fit(X_moons, y_moons)
X_test, y_test = make_moons(n_samples=1000, noise=0.2, random_state=43)
tree_clf1.score(X_test, y_test)   # 0.898  (overfits)
tree_clf2.score(X_test, y_test)   # 0.92   (regularized)

pca_pipeline = make_pipeline(StandardScaler(), PCA())
X_iris_rotated = pca_pipeline.fit_transform(X_iris)   # often simpler trees
```
- **What it demonstrates**: training, probabilities, regularization paying off on fresh data, and the PCA-rotation trick.

## Reference Tables
| Hyperparameter | Meaning | Regularize by |
|---|---|---|
| `max_depth` | Max tree depth (default None) | Decreasing |
| `max_features` | Features evaluated per split | Decreasing |
| `max_leaf_nodes` | Max number of leaves | Decreasing |
| `min_samples_split` | Min samples to split a node | Increasing |
| `min_samples_leaf` | Min samples per leaf | Increasing |
| `min_weight_fraction_leaf` | min_samples_leaf as weighted fraction | Increasing |
| `criterion` | "gini" / "entropy" / "log_loss" (clf); "squared_error" (reg) | – |

| Strength | Limitation |
|---|---|
| No scaling/centering needed | Axis-aligned (orthogonal) splits |
| Interpretable (white box) | High variance / instability |
| Fast O(log m) prediction | Greedy, not optimal |
| Handles multioutput | Overfits if unconstrained |

## Worked Example
**Reading the depth-2 iris tree**:
- Root: `petal length ≤ 2.45`? Yes → leaf (50 samples, pure *setosa*, gini = 0). No → node (100 samples).
- Depth 1 right: `petal width ≤ 1.75`? Yes → leaf: 54 samples, value [0, 49, 5] → *versicolor*, gini = 1 − (0/54)² − (49/54)² − (5/54)² ≈ **0.168**. No → leaf: 46 samples, mostly *virginica*.
- A flower 5 cm × 1.5 cm lands in the 54-sample leaf: P = [0/54, 49/54, 5/54] = [0, 0.907, 0.093] → class 1 (versicolor).
- With `max_depth=3` the tree would add splits at petal length 4.85 / 4.95 (dotted lines in the boundary plot).

**Regression tree** on y = x² + noise, `max_depth=2`: a new x = 0.2 follows the splits to a leaf whose prediction is the mean of its 110 training targets (0.111, MSE 0.015). An unregularized tree overfits wildly; `min_samples_leaf=10` gives a reasonable step function.

## Key Takeaways
1. Trees need no scaling and are interpretable; use them for explainability or as ensemble building blocks.
2. Always regularize (`max_depth`, `min_samples_leaf`, ...) and verify on held-out data.
3. Gini vs entropy rarely matters; keep the default Gini.
4. Rotate/decorrelate features with scaling + PCA when boundaries are diagonal.
5. Expect high variance; reduce it by averaging many trees (Ch 7).

## Connects To
- **Ch 2**: DecisionTreeRegressor overfitting housing (RMSE 0 on train).
- **Ch 7**: bagging/random forests/boosting built on CART trees; feature importance.
- **Ch 8**: PCA for rotation.
- **Fairness/interpretability**: white-box auditability.
