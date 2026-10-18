# Chapter 5: Support Vector Machines

## Core Idea
An SVM fits the **widest possible street** between classes (large margin classification), determined only by the **support vectors** on its edge. **Soft margins** (hyperparameter C) trade street width against violations. The **kernel trick** gives nonlinear boundaries without computing high-dimensional features. SVMs shine on **small-to-medium nonlinear datasets** (hundreds to thousands of instances) and scale poorly to large ones.

## Frameworks Introduced
- **Large margin classification**: maximize margin; adding instances "off the street" doesn't change the boundary.
- **Hard vs soft margin**: hard margin requires linear separability and is outlier-sensitive; soft margin balances margin size vs **margin violations** via `C`.
  - Low C: wider street, more violations, more regularization. High C: fewer violations, narrower street, risk of overfit.
  - Rule: **"If your SVM model is overfitting, you can try regularizing it by reducing C."**
- **Kernel selection rule of thumb**: **always try the linear kernel first** (`LinearSVC` is much faster than `SVC(kernel="linear")`). If the dataset isn't too large, try **Gaussian RBF** next; it usually works well. With spare time, try other kernels (polynomial, string kernels for text/DNA) using hyperparameter search.
- **Kernel trick**: K(a, b) = ϕ(a)ᵀϕ(b) computed without ϕ (e.g. polynomial degree 2: ϕ(a)ᵀϕ(b) = (aᵀb)²). It works only via the **dual problem**. **Mercer's theorem** guarantees ϕ exists for valid kernels.
- **SVM regression (ε-insensitive)**: reverse the objective. Fit as many instances as possible *on* the street with width ε; points inside the margin don't affect the model. Reducing ε increases support vectors.

## Key Concepts
- **Support vectors**: instances on or inside the street; only they determine the model and predictions.
- **Decision function**: wᵀx + b. Predict positive if ≥ 0; the street borders are at ±1. A smaller ‖w‖ gives a wider margin (margin = 2/‖w‖).
- **Slack variables ζ⁽ⁱ⁾**: per-instance allowed violation; C weights Σζ against ½‖w‖².
- **Hinge loss** max(0, 1 − t·s): zero when off the street on the correct side; GD alternative to QP solvers (`SGDClassifier(loss="hinge")`).
- **Quadratic programming (QP)**: convex quadratic objective with linear constraints; hard/soft margin SVMs are QP problems.
- **Dual problem**: faster when m < n and enables kernels. Predictions use only the support vectors: ŷ = Σα⁽ⁱ⁾t⁽ⁱ⁾K(x⁽ⁱ⁾, x) + b.
- **Gaussian RBF similarity** φ(x, ℓ) = exp(−γ‖x − ℓ‖²); using every instance as a landmark makes m features (linearly separable, but expensive). The RBF kernel does this implicitly.
- **`gamma` (γ)**: RBF bell width. Higher γ means a narrower bell, more irregular boundary, and overfit risk; it acts like a regularization knob (reduce it if overfitting).
- **`coef0`**: polynomial kernel's weighting of high- vs low-degree terms.
- **Probabilities**: `LinearSVC` has none; `SVC(probability=True)` calibrates via 5-fold CV logistic regression (slower), adding `predict_proba()`.

## Mental Models
- Think of an SVM as a **road-builder**: it cares only about the cars parked at the edge (support vectors), not traffic far away.
- **Two knobs, opposite directions**: high C and high γ → complex/overfit; low C and low γ → smooth/underfit. Tune them together (randomized search), but know what they do to narrow the range.
- **Polynomial features vs polynomial kernel**: explicit features explode combinatorially at high degree; the kernel gets the same effect without the explosion.
- **Scale first**: SVMs are very sensitive to feature scales (an unscaled axis dominates street orientation).

## Anti-patterns
- **Skipping StandardScaler**: wrong street orientation.
- **Using `SVC` on hundreds of thousands of instances**: O(m²n)–O(m³n), dreadfully slow. Use `LinearSVC`, `SGDClassifier`, or another model family.
- **High-degree polynomial kernel when overfitting**: reduce the degree.
- **Expecting `predict_proba` from LinearSVC**.
- **Hard margin with outliers**: one outlier can make the margin tiny or impossible.

## Code Examples
```python
from sklearn.svm import LinearSVC, SVC
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

svm_clf = make_pipeline(StandardScaler(), LinearSVC(C=1, random_state=42))
poly_kernel_svm_clf = make_pipeline(StandardScaler(),
                                    SVC(kernel="poly", degree=3, coef0=1, C=5))
rbf_kernel_svm_clf = make_pipeline(StandardScaler(),
                                   SVC(kernel="rbf", gamma=5, C=0.001))

from sklearn.svm import LinearSVR, SVR
svm_reg = make_pipeline(StandardScaler(), LinearSVR(epsilon=0.5, random_state=42))
svm_poly_reg = make_pipeline(StandardScaler(),
                             SVR(kernel="poly", degree=2, C=0.01, epsilon=0.1))
```
- **What it demonstrates**: the four SVM configurations (linear/kernel × classification/regression), always behind a scaler.

## Reference Tables
| Class | Time complexity | Out-of-core | Scaling required | Kernel trick |
|---|---|---|---|---|
| `LinearSVC` | O(m × n) | No | Yes | No |
| `SVC` | O(m² × n) to O(m³ × n) | No | Yes | Yes |
| `SGDClassifier` | O(m × n) | Yes | Yes | No |

| Hyperparameter | Increase it → | When overfitting |
|---|---|---|
| `C` | fewer violations, narrower margin | Reduce |
| `gamma` (RBF) | narrower bells, wigglier boundary | Reduce |
| `degree` (poly) | more complex boundary | Reduce |
| `epsilon` (SVR) | wider tube, fewer support vectors | (regularizes when reduced) |

## Worked Example
**Moons dataset** (`make_moons(n_samples=100, noise=0.15)`):
1. Linear SVC fails: the data isn't linearly separable.
2. *Explicit features*: `PolynomialFeatures(degree=3)` → `StandardScaler` → `LinearSVC(C=10, max_iter=10_000)` gives a curved boundary that works.
3. *Poly kernel*: `SVC(kernel="poly", degree=3, coef0=1, C=5)` gives the same effect with no feature explosion; degree 10 overfits.
4. *RBF kernel* grid of γ ∈ {0.1, 5} × C ∈ {0.001, 1000}: γ = 0.1, C = 0.001 is smooth (underfit-ish); γ = 5, C = 1000 is wiggly islands around instances (overfit). Pick between them via CV.
5. *Similarity-feature intuition*: 1D x = −1 with landmarks at −2 and 1, γ = 0.3: features exp(−0.3·1²) ≈ 0.74 and exp(−0.3·2²) ≈ 0.30. The data becomes linearly separable in the new space.

## Key Takeaways
1. Scale features; start with `LinearSVC`, then RBF `SVC` if the data is small/medium.
2. C and γ both regularize when reduced; tune them jointly with randomized search.
3. The kernel trick works through the dual problem; predictions only involve the support vectors.
4. SVR is ε-insensitive: it fits a tube; reducing ε adds support vectors.
5. For large datasets, use `SGDClassifier(loss="hinge")` (out-of-core) or tree ensembles / NNs.
6. SVMs also do novelty detection (One-Class SVM, Ch 9).

## Connects To
- **Ch 2**: RBF similarity features (`ClusterSimilarity`).
- **Ch 3**: OvO for multiclass SVC (scales poorly with m).
- **Ch 4**: polynomial features, hinge loss vs log loss, linear models.
- **Ch 9**: novelty detection.
