# Chapter 2: End-to-End Machine Learning Project

## Core Idea
A real ML project follows eight steps: frame, get data, explore, prepare, train, fine-tune, present, launch and monitor. Most of the value and work is in framing the problem and building a **reproducible Scikit-Learn preprocessing pipeline**, so the same transformations run in training, tuning, and production. Worked through on California Housing (predict a district's median house value).

## Frameworks Introduced
- **The 8 main steps** (from Appendix A checklist):
  1. Look at the big picture. 2. Get the data. 3. Explore and visualize to gain insights. 4. Prepare the data. 5. Select a model and train it. 6. Fine-tune. 7. Present your solution. 8. Launch, monitor, maintain.
- **Frame the Problem first**: ask (a) what's the business objective (how will the output be used downstream?), (b) what's the current solution and its performance (experts were >30% off, which sets the baseline), then classify the task: supervised / multiple regression / univariate / batch.
- **Check the Assumptions**: list and verify assumptions with downstream consumers (e.g. if they actually turn prices into categories, it's a classification task, not regression).
- **Scikit-Learn Design principles**: *Consistency* (Estimators `fit()`, Transformers `transform()`/`fit_transform()`, Predictors `predict()`/`score()`), *Inspection* (hyperparams as public attrs, learned params with trailing `_`), *Nonproliferation of classes* (NumPy/SciPy arrays), *Composition* (Pipelines), *Sensible defaults*.
- **Stratified sampling on the most important feature**: bin it (e.g. `income_cat` with 5 bins) so every stratum is represented in the test set.
- **Feature transformation ladder for skewed/multimodal features**: log / sqrt / power to shrink heavy tails; bucketize (percentiles); Gaussian **RBF similarity** features for modes; then scale.

## Key Concepts
- **RMSE vs MAE**: RMSE (ℓ2) weights large errors more; prefer MAE (ℓ1) with many outliers. Higher norm index means more focus on large values.
- **Data snooping bias**: looking at the test set leads you to pick models that overfit it, giving over-optimistic estimates.
- **Imputation**: `SimpleImputer(strategy="median"|"mean"|"most_frequent"|"constant")`; also `KNNImputer`, `IterativeImputer`.
- **One-hot vs ordinal encoding**: `OrdinalEncoder` implies an ordering; `OneHotEncoder` doesn't, and remembers categories (unlike `pd.get_dummies`); `handle_unknown="ignore"`.
- **Min-max scaling vs standardization**: `MinMaxScaler` (0–1 or -1–1) is sensitive to outliers; `StandardScaler` is not range-bound and is robust-ish. Fit **only** on the training set.
- **`TransformedTargetRegressor`**: scale/log the target and inverse-transform predictions automatically.
- **`ColumnTransformer`**: apply different pipelines to different columns; `remainder=`, `"drop"`, `"passthrough"`, `make_column_selector(dtype_include=...)`.
- **Cross-validation (k-fold)**: `cross_val_score(..., scoring="neg_root_mean_squared_error", cv=10)`; scores are utilities, so negate them.
- **GridSearchCV / RandomizedSearchCV / HalvingGridSearchCV**: hyperparameter search; address nested params with `step__substep__param`.

## Mental Models
- **Pipeline = the unit of deployment**: anything not in the pipeline won't happen in production. Put preprocessing in the pipeline so it can also be *tuned* (preprocessing and model hyperparameters interact).
- **Use randomized search over grid search** when the space is large: 1,000 iterations try 1,000 values of each continuous param, an irrelevant param doesn't multiply cost, and you control the budget.
- **If the best value is at the edge of the grid, extend the grid** (n_clusters=15 was the max, so search higher).
- **Correlation ≠ dependence**: Pearson's r measures only *linear* relationships and says nothing about slope.
- **A capped target is a scoping question**: if consumers need predictions above $500k, either get proper labels or drop capped districts from *both* train and test.

## Anti-patterns
- **Exploring before splitting**: create the test set first, put it aside, and never look at it.
- **Unstable random splits**: re-running `permutation` leaks the full set over time. Use a fixed seed or hash of a stable ID (`crc32(id) < ratio * 2**32`).
- **Calling `fit()` on validation/test/new data**: fit scalers/imputers on training data only.
- **`pd.get_dummies` in production**: different columns for unseen/missing categories.
- **One-hot encoding high-cardinality categoricals**: too many features. Replace with meaningful numeric features (distance to ocean, country GDP) or learned embeddings (Ch 13).
- **Trusting training-set error**: the decision tree's RMSE of 0 is pure overfitting, revealed by CV (~66,868).
- **Tweaking after seeing test results**: the improvements won't generalize.

## Code Examples
```python
def column_ratio(X):
    return X[:, [0]] / X[:, [1]]

def ratio_name(function_transformer, feature_names_in):
    return ["ratio"]

def ratio_pipeline():
    return make_pipeline(SimpleImputer(strategy="median"),
                         FunctionTransformer(column_ratio, feature_names_out=ratio_name),
                         StandardScaler())

log_pipeline = make_pipeline(SimpleImputer(strategy="median"),
                             FunctionTransformer(np.log, feature_names_out="one-to-one"),
                             StandardScaler())
cluster_simil = ClusterSimilarity(n_clusters=10, gamma=1., random_state=42)
cat_pipeline = make_pipeline(SimpleImputer(strategy="most_frequent"),
                             OneHotEncoder(handle_unknown="ignore"))
default_num_pipeline = make_pipeline(SimpleImputer(strategy="median"), StandardScaler())

preprocessing = ColumnTransformer([
    ("bedrooms", ratio_pipeline(), ["total_bedrooms", "total_rooms"]),
    ("rooms_per_house", ratio_pipeline(), ["total_rooms", "households"]),
    ("people_per_house", ratio_pipeline(), ["population", "households"]),
    ("log", log_pipeline, ["total_bedrooms", "total_rooms", "population",
                           "households", "median_income"]),
    ("geo", cluster_simil, ["latitude", "longitude"]),
    ("cat", cat_pipeline, make_column_selector(dtype_include=object)),
], remainder=default_num_pipeline)   # housing_median_age
```
- **What it demonstrates**: the complete production preprocessing (impute, ratio features, log tails, k-means RBF geo-features, one-hot, scale) as one tunable object. It outputs 24 features.

```python
class ClusterSimilarity(BaseEstimator, TransformerMixin):
    def __init__(self, n_clusters=10, gamma=1.0, random_state=None):  # no *args/**kwargs
        self.n_clusters = n_clusters
        self.gamma = gamma
        self.random_state = random_state

    def fit(self, X, y=None, sample_weight=None):     # y needed for pipelines
        self.kmeans_ = KMeans(self.n_clusters, random_state=self.random_state)
        self.kmeans_.fit(X, sample_weight=sample_weight)
        return self                                     # always return self

    def transform(self, X):
        return rbf_kernel(X, self.kmeans_.cluster_centers_, gamma=self.gamma)

    def get_feature_names_out(self, names=None):
        return [f"Cluster {i} similarity" for i in range(self.n_clusters)]
```
- **What it demonstrates**: the custom transformer contract. `BaseEstimator` gives `get_params`/`set_params` (needed for search), and `TransformerMixin` gives `fit_transform`. Validate with `check_estimator()`.

```python
full_pipeline = Pipeline([("preprocessing", preprocessing),
                          ("random_forest", RandomForestRegressor(random_state=42))])
param_distribs = {"preprocessing__geo__n_clusters": randint(low=3, high=50),
                  "random_forest__max_features": randint(low=2, high=20)}
rnd_search = RandomizedSearchCV(full_pipeline, param_distributions=param_distribs,
                                n_iter=10, cv=3, scoring="neg_root_mean_squared_error",
                                random_state=42)
rnd_search.fit(housing, housing_labels)
```

## Reference Tables
| Model (default params) | Train RMSE | 10-fold CV RMSE | Verdict |
|---|---|---|---|
| LinearRegression | 68,688 | ~69k | Underfits |
| DecisionTreeRegressor | 0 | 66,868 ± 2,061 | Overfits badly |
| RandomForestRegressor | ~17,474 | 47,020 ± 1,034 | Promising, still overfits |
| RF + GridSearch (n_clusters=15, max_features=6) | – | 44,042 | Tuned |
| Final model on test set | – | **41,424** (95% CI 39,275–43,467) | Launch |

| Scaling choice | Use when |
|---|---|
| `StandardScaler` | Default; robust to outliers vs min-max; use `with_mean=False` for sparse |
| `MinMaxScaler(feature_range=(-1,1))` | Bounded inputs needed (NNs like zero-mean) |
| log / sqrt / power then scale | Heavy-tailed positive features |
| Bucketize (percentiles) | Heavy tails; nearly uniform result |
| RBF similarity to modes | Multimodal features (e.g. age peak at 35) |

## Worked Example
**Diagnosing California Housing data** (`housing.info()`, `hist()`):
- 20,640 districts, 10 attributes; `total_bedrooms` has 207 missing → impute median.
- `median_income` is scaled (in ~$10k) and capped at 15 / 0.5; `housing_median_age` and **`median_house_value` (the target) are capped at $500k**, so check with the downstream team.
- Very different scales → standardize. Right-skewed histograms → log transform.
- `ocean_proximity` is categorical (5 values, ISLAND has 5) → one-hot.
- Stratify on `pd.cut(median_income, [0,1.5,3,4.5,6,inf])`: the random split skews category proportions; the stratified split matches the population.
- Correlation with target: `median_income` 0.69 ≫ others. Engineered `bedrooms_ratio` (−0.26) beats raw `total_rooms` (0.13).
- Geo scatter (`alpha=0.2`, size=population, color=price) shows price tied to the coast and density, which motivates the k-means geo-similarity features.
- Feature importances (RF): `log__median_income` 0.19, `INLAND` 0.07, `bedrooms_ratio` 0.07. Only one ocean category matters, so try dropping the others (`SelectFromModel`).

## Key Takeaways
1. Start every project from the checklist (App A) and frame the business objective and current baseline first.
2. Split (stratified, reproducible) **before** exploring; explore only a copy of the training set.
3. Engineer ratios and combinations; check correlations; iterate after a first prototype.
4. Encode all preprocessing as Scikit-Learn transformers in a `ColumnTransformer` and full `Pipeline`, then tune preprocessing and model together.
5. Evaluate with k-fold CV; shortlist 2–5 models before tuning; prefer randomized search.
6. Check error on subsets (rural/urban, rich/poor) before launch; report the test RMSE with a 95% confidence interval and don't tweak afterward.
7. In production: `joblib.dump` the whole pipeline (custom classes must be importable), automate retraining, monitor both live performance **and input quality**, keep backups and roll back.

## Connects To
- **App A**: the full checklist these steps follow.
- **Ch 3**: evaluation for classification (precision/recall, confusion matrix).
- **Ch 7**: random forests and ensembles used here.
- **Ch 9**: k-means behind `ClusterSimilarity`.
- **Ch 13/19**: Keras preprocessing layers and deploying on Vertex AI.
