# Chapter 4: Training Models

## Core Idea
Opens the black box. Linear models are trained either in **closed form** (Normal equation / SVD) or by **gradient descent** (batch, stochastic, mini-batch). You diagnose under/overfitting with **learning curves** and the **bias/variance trade-off**, and constrain models with **ridge, lasso, elastic net, early stopping**. Logistic and softmax regression extend the same machinery to classification.

## Frameworks Introduced
- **Closed form vs gradient descent**:
  - Normal equation θ̂ = (XᵀX)⁻¹Xᵀy, or SVD pseudoinverse θ̂ = X⁺y (`LinearRegression` uses `lstsq`). O(n^2.4–n³) in features, O(m) in instances, and the data must fit in RAM.
  - GD scales with features and supports out-of-core training. It needs a learning rate and iterations.
- **Gradient descent family**: step θ ← θ − η∇θMSE(θ).
  - *Batch GD*: full training set per step; exact but slow on large m. Converges with fixed η in O(1/ε).
  - *Stochastic GD*: one random instance per step; fast, can escape local minima, but bounces around the minimum, so use a **learning schedule** (simulated annealing), e.g. η = t0/(t + t1).
  - *Mini-batch GD*: small random batches; GPU-friendly, less erratic than SGD.
- **Learning curves diagnosis** (`learning_curve`): plot train vs validation error vs training set size.
  - Both curves plateau high and close → **underfitting**; more data won't help, so use a better model or features.
  - Low train error with a gap to validation → **overfitting**; more data narrows the gap, or regularize.
- **Bias/Variance trade-off**: generalization error = **bias** (wrong assumptions → underfit) + **variance** (sensitivity to small data variations → overfit) + **irreducible error** (noise; fix the data). More complexity means more variance and less bias.
- **Regularization ladder**: "It is almost always preferable to have at least a little bit of regularization":
  - *Ridge* (ℓ2, `Ridge(alpha)`): a good default.
  - *Lasso* (ℓ1, `Lasso(alpha)`): drives unimportant weights to exactly 0 → automatic feature selection, sparse models. Use it if you suspect only a few features matter.
  - *Elastic Net* (`ElasticNet(alpha, l1_ratio)`): prefer it over lasso when features > instances or features are strongly correlated (lasso is erratic there).
  - *Early stopping*: stop when validation error reaches its minimum. Hinton called it a "beautiful free lunch".

## Key Concepts
- **Loss vs metric**: the training loss should be easy to optimize and correlated with the metric, which should match the business objective (e.g. train with log loss, evaluate with precision/recall).
- **Convexity**: MSE for linear regression and log loss for logistic regression are convex, so GD finds the global minimum given a reasonable η.
- **Epoch**: one pass over the training set.
- **IID requirement for SGD**: shuffle, or SGD optimizes for one label at a time.
- **`partial_fit` / `warm_start`**: incremental training in Scikit-Learn.
- **PolynomialFeatures(degree=d)**: n features become (n+d)!/(d!n!) features, a combinatorial explosion. It includes interaction terms.
- **Logistic (sigmoid) function** σ(t) = 1/(1+e^(−t)); **logit** t = log(p/(1−p)) is the log-odds.
- **Log loss**: −[y log p̂ + (1−y) log(1−p̂)]; no closed form, but convex.
- **Softmax regression**: per-class scores sₖ(x) = θₖᵀx, then p̂ₖ = exp(sₖ)/Σexp(sⱼ); trained with **cross entropy**. Only for mutually exclusive classes.
- **`C`** in `LogisticRegression` = inverse regularization strength (higher C = less regularization); ℓ2 by default.

## Mental Models
- Think of GD as **descending a foggy mountain by the steepest slope**. With **unscaled features** the bowl is elongated, so GD zig-zags and takes a long march. Always `StandardScaler` before GD and before regularized models.
- Think of **training as a search in parameter space**: more parameters mean a harder search (a needle in a 300-D haystack). Convexity guarantees the needle is at the bottom of the bowl.
- **Learning rate tuning**: too small means slow; too high means divergence. Grid-search η with a limited number of epochs; set many epochs and stop when the gradient norm < tolerance ε.
- **Lasso's diamond vs ridge's circle**: the ℓ1 penalty's gradients are ±1, so it pushes weights to hit 0 along axes. The ℓ2 penalty's gradient shrinks near the origin, so weights shrink smoothly but rarely reach 0.
- **Early stopping with noisy curves**: stop after validation error has been above its minimum for a while, then roll back to the best checkpoint.

## Anti-patterns
- **Normal equation with 100k+ features**: too slow; use GD.
- **Regularizing the bias term**: the sum starts at i = 1.
- **Using `alpha` in SGDRegressor like Ridge's**: SGD's penalty is not divided by m, so use `alpha=0.1/m` to match.
- **More data for an underfitting model**: wasted effort.
- **Plain linear regression in production**: almost always add some regularization.
- **Softmax for multilabel**: it predicts exactly one class.

## Code Examples
```python
eta = 0.1          # learning rate
n_epochs = 1000
m = len(X_b)       # X_b = add_dummy_feature(X)  (x0 = 1)
np.random.seed(42)
theta = np.random.randn(2, 1)
for epoch in range(n_epochs):
    gradients = 2 / m * X_b.T @ (X_b @ theta - y)
    theta = theta - eta * gradients
# theta ≈ [[4.215], [2.770]] — same as the Normal equation
```
- **What it demonstrates**: batch GD in four lines, converging to the closed-form solution.

```python
from copy import deepcopy
preprocessing = make_pipeline(PolynomialFeatures(degree=90, include_bias=False),
                              StandardScaler())
X_train_prep = preprocessing.fit_transform(X_train)
X_valid_prep = preprocessing.transform(X_valid)
sgd_reg = SGDRegressor(penalty=None, eta0=0.002, random_state=42)
best_valid_rmse = float('inf')
for epoch in range(500):
    sgd_reg.partial_fit(X_train_prep, y_train)
    val_error = mean_squared_error(y_valid, sgd_reg.predict(X_valid_prep), squared=False)
    if val_error < best_valid_rmse:
        best_valid_rmse = val_error
        best_model = deepcopy(sgd_reg)
```
- **What it demonstrates**: early stopping by hand with `partial_fit` and checkpointing the best model.

## Reference Tables
| Algorithm | Large m | Out-of-core | Large n | Hyperparams | Scikit-Learn |
|---|---|---|---|---|---|
| Normal equation | Fast | No | Slow | 0 | N/A |
| SVD | Fast | No | Slow | 0 | `LinearRegression` |
| Batch GD | Slow | No | Fast | 2 | N/A |
| Stochastic GD | Fast | Yes | Fast | ≥2 | `SGDRegressor` |
| Mini-batch GD | Fast | Yes | Fast | ≥2 | N/A |

| Regularizer | Penalty | Effect | Use when |
|---|---|---|---|
| Ridge | α Σθ²/m... (ℓ2²) | Shrinks weights | Default |
| Lasso | 2α Σ\|θ\| (ℓ1) | Zeroes weights (sparse) | Few useful features |
| Elastic Net | r·ℓ1 + (1−r)/2·ℓ2² | Mix | n > m or correlated features |
| Early stopping | – | Stop at min validation error | Any iterative learner |

## Worked Example
**Diagnosing with learning curves on y = 0.5x² + x + 2 + noise** (m = 100):
1. *Linear model*: training error starts at 0 (fits 1–2 points), rises to a plateau; validation error starts huge, falls, and plateaus close to training error at a high value. Both are high and close, so it's **underfitting**. Adding data won't help.
2. *10th-degree polynomial*: training error much lower, and a clear **gap** remains, the hallmark of **overfitting**. More data would close it.
3. *300-degree polynomial*: wiggles through the training points (severe overfit).
4. *2nd-degree polynomial* (`PolynomialFeatures(degree=2)` + `LinearRegression`): learns ŷ = 0.56x² + 0.93x + 1.78, close to the truth (0.5, 1.0, 2.0). This is the right capacity.
5. Lasso with α = 0.01 on degree-10 features gives a roughly cubic curve: the high-degree weights are zeroed, so it has selected its own features.

## Key Takeaways
1. Use closed form for small n; GD (mini-batch/SGD) for many features or out-of-core data.
2. Scale features before GD and before any regularized model.
3. Use a learning schedule with SGD and shuffle every epoch (IID).
4. Read learning curves: high-and-close means a bigger model or better features; a gap means more data or regularization.
5. Default to Ridge; Lasso/ElasticNet when you expect few relevant features; always consider early stopping.
6. Logistic regression outputs calibrated-ish probabilities via sigmoid with log loss; softmax handles mutually exclusive multiclass via cross entropy.
7. Use `RidgeCV`, `LassoCV`, `ElasticNetCV` for fast built-in CV tuning.

## Connects To
- **Ch 1**: regularization and hyperparameters, intuitively.
- **Ch 3**: `SGDClassifier`, decision functions, thresholds.
- **Ch 5**: SVMs as another linear model with a different loss (hinge).
- **Ch 10–11**: GD, mini-batches, softmax/cross entropy, early stopping, and schedules all reappear in deep learning.
