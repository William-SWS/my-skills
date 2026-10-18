# Chapter 7: Ensemble Learning and Random Forests

## Core Idea
Aggregating many diverse predictors (the **wisdom of the crowd**) usually beats the best single one. Get diversity from different algorithms (**voting**), different data samples (**bagging/pasting**, **random forests**, **extra-trees**), or sequential error correction (**boosting**: AdaBoost, gradient boosting, HGB). Learn the aggregator itself with **stacking**. Random forests, AdaBoost, and GBRT are among the first models to try on tabular data. Ensembles are typically used near the end of a project, once you have several good predictors.

## Frameworks Introduced
- **Law of large numbers for classifiers**: 1,000 independent classifiers at 51% each can reach ~75% by majority vote. This holds *only if errors are independent*, so diversify algorithms and data.
- **Hard vs soft voting** (`VotingClassifier`): hard = majority class; soft = average `predict_proba`, which gives more weight to confident votes and usually performs better (needs probabilities, e.g. `SVC(probability=True)`).
- **Bagging vs pasting**: sample training subsets with replacement (bagging = bootstrap aggregating) or without (pasting). Aggregate by mode (classification) / mean (regression). Each predictor has higher bias but the ensemble has similar bias and **lower variance**. Bagging generally gives better models; compare both with CV if you have time.
- **Out-of-bag (OOB) evaluation**: with bootstrap, ~63% of instances are sampled per predictor (1 − e⁻¹); the other ~37% serve as a free validation set (`oob_score=True`).
- **Random patches / random subspaces**: also sample *features* (`max_features`, `bootstrap_features`): patches = sample instances + features; subspaces = all instances, sampled features. Useful for high-dimensional inputs (images).
- **Random forest**: bagged trees, each split searched over a random subset of √n features, giving more diversity (more bias, less variance).
- **Extra-Trees (Extremely Randomized Trees)**: also random *thresholds*, so it trains much faster. Whether it beats RF is unpredictable; try both with CV.
- **Boosting**: sequential predictors, each correcting its predecessor. **Cannot be parallelized**.
  - *AdaBoost*: reweight misclassified instances; predictor weight αⱼ = η log((1 − rⱼ)/rⱼ). SAMME / SAMME.R for multiclass.
  - *Gradient Boosting*: fit each new predictor to the **residual errors** of the previous ensemble; sum the predictions.
- **Shrinkage**: a low `learning_rate` (e.g. 0.05) needs more trees but generalizes better; combine with early stopping (`n_iter_no_change`).
- **Stacking**: train a **blender (meta-learner)** on out-of-sample predictions (via `cross_val_predict`) of the base predictors. Layers of blenders are possible.

## Key Concepts
- **Weak learner**: only slightly better than random; **strong learner**: high accuracy.
- **Decision stump**: tree with `max_depth=1`, AdaBoost's default base estimator.
- **Feature importance**: weighted average impurity reduction of nodes using a feature, normalized to sum to 1 (`feature_importances_`). Handy for feature selection.
- **Stochastic gradient boosting**: `subsample=0.25` trains each tree on 25% of instances, trading bias for variance and speed.
- **HistGradientBoosting (HGB)**: bins features (`max_bins` ≤ 255) so training is O(b × m); hundreds of times faster on large data; natively handles **categorical features and missing values**; early stopping auto-on when m > 10,000; `max_iter` replaces `n_estimators`.
- **XGBoost, CatBoost, LightGBM, TF Random Forests**: optimized external GBRT/forest libraries with GPU support.

## Mental Models
- Think of **diversity as the whole game**: three models at 86–90% gave a 91.2% hard vote and 92% soft vote; correlated models add nothing.
- **Bagging attacks variance; boosting attacks bias** (and variance, with shrinkage and subsampling).
- **AdaBoost ≈ gradient descent in function space**: instead of tweaking one predictor's parameters, it adds predictors to the ensemble.
- **Stacking's blender must be trained on out-of-fold predictions**, or it learns to trust overfit base models.
- **If AdaBoost overfits**: reduce `n_estimators` or regularize the base estimator more.
- **If GBRT overfits**: lower `learning_rate` with more trees and early stopping, `subsample` < 1, shallower trees.

## Anti-patterns
- **Ensembling near-identical models**: correlated errors, no gain.
- **Using SVMs as AdaBoost base learners**: slow and unstable.
- **Setting `n_iter_no_change` too low** (stops early → underfit) or too high (→ overfit).
- **One-hot encoding for HGB**: use `OrdinalEncoder` + `categorical_features=` instead; no imputer or scaler needed.
- **Expecting boosting to scale like bagging**: it's sequential.

## Code Examples
```python
voting_clf = VotingClassifier(estimators=[
    ("lr", LogisticRegression(random_state=42)),
    ("rf", RandomForestClassifier(random_state=42)),
    ("svc", SVC(probability=True, random_state=42))], voting="soft")

bag_clf = BaggingClassifier(DecisionTreeClassifier(), n_estimators=500,
                            oob_score=True, n_jobs=-1, random_state=42)
rnd_clf = RandomForestClassifier(n_estimators=500, max_leaf_nodes=16,
                                 n_jobs=-1, random_state=42)
ada_clf = AdaBoostClassifier(DecisionTreeClassifier(max_depth=1),
                             n_estimators=30, learning_rate=0.5, random_state=42)
gbrt_best = GradientBoostingRegressor(max_depth=2, learning_rate=0.05,
                                      n_estimators=500, n_iter_no_change=10,
                                      random_state=42)          # stops at 92 trees
hgb_reg = make_pipeline(
    make_column_transformer((OrdinalEncoder(), ["ocean_proximity"]),
                            remainder="passthrough"),
    HistGradientBoostingRegressor(categorical_features=[0], random_state=42))
stacking_clf = StackingClassifier(
    estimators=[("lr", LogisticRegression(random_state=42)),
                ("rf", RandomForestClassifier(random_state=42)),
                ("svc", SVC(probability=True, random_state=42))],
    final_estimator=RandomForestClassifier(random_state=43), cv=5)
```
- **What it demonstrates**: every ensemble family in Scikit-Learn with the book's settings. The HGB housing pipeline needs no imputer, scaler or one-hot encoder (RMSE ≈ 47,600 untuned).

## Reference Tables
| Method | Diversity source | Parallel | Reduces | Key hyperparams |
|---|---|---|---|---|
| Voting | Different algorithms | Yes | Variance | `voting="hard"/"soft"` |
| Bagging/Pasting | Bootstrap/no-replace samples | Yes | Variance | `n_estimators`, `max_samples`, `bootstrap`, `oob_score` |
| Random Forest | Bagging + √n feature subsets | Yes | Variance | tree params + `n_estimators`, `max_features` |
| Extra-Trees | + random thresholds | Yes | Variance (faster) | same as RF; `bootstrap=False` |
| AdaBoost | Reweighted instances | No | Bias | `n_estimators`, `learning_rate`, base depth |
| Gradient Boosting | Residual fitting | No | Bias (+var w/ shrinkage) | `learning_rate`, `n_estimators`, `max_depth`, `subsample`, `n_iter_no_change` |
| HGB | Binned GBRT | No (fast) | Bias | `max_iter`, `max_bins`, `max_leaf_nodes`, `categorical_features` |
| Stacking | Learned blender | Partly | Both | `final_estimator`, `cv` |

| Moons test accuracy | Score |
|---|---|
| LogReg / RF / SVC | 0.864 / 0.896 / 0.896 |
| Hard voting | 0.912 |
| Soft voting | 0.920 |
| Bagging 500 trees (OOB est. 0.896) | 0.920 |
| Stacking (RF blender) | 0.928 |

## Worked Example
**Gradient boosting by hand** on y = 3x² + noise:
```python
tree_reg1 = DecisionTreeRegressor(max_depth=2, random_state=42).fit(X, y)
y2 = y - tree_reg1.predict(X)                      # residuals
tree_reg2 = DecisionTreeRegressor(max_depth=2, random_state=43).fit(X, y2)
y3 = y2 - tree_reg2.predict(X)
tree_reg3 = DecisionTreeRegressor(max_depth=2, random_state=44).fit(X, y3)
X_new = np.array([[-0.4], [0.], [0.5]])
sum(tree.predict(X_new) for tree in (tree_reg1, tree_reg2, tree_reg3))
# array([0.49484029, 0.04021166, 0.75026781])
```
Row by row: one tree is a crude step; adding tree 2 (fit to residuals) refines it; with 3 trees the ensemble tracks the parabola. This equals `GradientBoostingRegressor(max_depth=2, n_estimators=3, learning_rate=1.0)`. With `learning_rate=0.05`, too few trees underfit and too many overfit; early stopping picked **92 trees** out of 500.

## Key Takeaways
1. Try RF, Extra-Trees and (Hist)GradientBoosting early on any tabular problem.
2. Maximize ensemble diversity (algorithms, samples, features); prefer soft voting when probabilities exist.
3. Use OOB score as a free validation estimate for bagging/RF (slightly pessimistic).
4. GBRT recipe: small learning rate, many trees, early stopping, `subsample` < 1.
5. Use HGB for large datasets with categoricals/missing values; consider XGBoost/LightGBM/CatBoost.
6. Use RF `feature_importances_` for quick feature insight/selection.
7. Stacking with out-of-fold predictions often squeezes out the last bit of accuracy.

## Connects To
- **Ch 2**: RF on housing, ensemble tuning, `SelectFromModel`.
- **Ch 4**: bias/variance, early stopping, learning rate.
- **Ch 6**: decision trees as base learners.
- **Ch 11**: MC dropout as an implicit ensemble.
