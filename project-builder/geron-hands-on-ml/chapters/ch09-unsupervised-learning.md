# Chapter 9: Unsupervised Learning Techniques

## Core Idea
Most data is unlabeled. Unsupervised learning extracts value from it through **clustering** (k-means, DBSCAN, others), **density estimation** (Gaussian mixtures), and **anomaly/novelty detection**. Clustering also powers feature engineering, dimensionality reduction, image segmentation and especially **semi-supervised learning**: label a few representative instances, then propagate the labels. Yann LeCun: "if intelligence was a cake, unsupervised learning would be the cake."

## Frameworks Introduced
- **k-means (Lloyd–Forgy)**: init centroids, assign instances to the nearest centroid, update centroids to cluster means, repeat until stable. It's guaranteed to converge, possibly to a local optimum.
  - Mitigate: **k-means++** init (default; picks distant centroids with probability ∝ D(x)²), `n_init` runs keeping the lowest **inertia**, or a known `init` array with `n_init=1`.
  - Speed: Elkan's accelerated k-means (triangle inequality); **MiniBatchKMeans** (3–4× faster, slightly worse inertia, out-of-core via memmap/`partial_fit`).
- **Choosing k**: the inertia **elbow** is coarse; prefer **silhouette score** (mean of (b − a)/max(a, b), from −1 to +1) and **silhouette diagrams** (knife shapes: all clusters should extend past the mean score with similar sizes).
- **Clustering for semi-supervised learning** (worked example below): cluster into k groups, label only the **representative instance** (closest to each centroid), **propagate** labels to cluster members, and drop the farthest 1% as likely mislabeled.
- **Active learning (uncertainty sampling)**: train, predict unlabeled data, have experts label the most uncertain (lowest estimated probability) instances, repeat until gains stop. Alternatives: largest model change, largest validation drop, or model disagreement.
- **DBSCAN**: clusters are continuous regions of high density. Instances with ≥ `min_samples` neighbors within `eps` are **core instances**; neighbors of cores join the cluster; others are anomalies (label −1). It finds any shape/number of clusters and is robust to outliers, but struggles with varying densities (try **HDBSCAN**). It has no `predict()`, so train a `KNeighborsClassifier` on the core instances.
- **Gaussian Mixture Models (GMM) via Expectation-Maximization**: E-step computes **responsibilities** (soft assignments); M-step updates weights ϕ, means μ, covariances Σ. It's a generative model (`sample()`), supports density (`score_samples` = log PDF), hard (`predict`) and soft (`predict_proba`) clustering.
  - Constrain covariance when EM struggles: `"spherical"`, `"diag"`, `"tied"`, `"full"` (default).
  - **Select k with BIC/AIC** (lower is better); BIC picks simpler models. Or use **`BayesianGaussianMixture`**, which zeroes out unnecessary cluster weights.
- **Anomaly vs novelty detection**: anomaly detection trains on possibly contaminated data; novelty detection assumes a clean training set.

## Key Concepts
- **Hard vs soft clustering**: one cluster per instance vs per-cluster scores. `kmeans.transform()` gives distances to the centroids, which work as an efficient nonlinear dimensionality reduction.
- **Inertia**: sum of squared distances to the nearest centroid (`score()` returns its negative).
- **Voronoi tessellation**: k-means decision boundaries.
- **Image color segmentation**: cluster pixel colors and replace them with centroid colors (small, distinct regions such as a ladybug's red may vanish at small k). Compare *semantic* and *instance* segmentation (CNNs, Ch 14).
- **Label propagation**: `LabelSpreading`, `LabelPropagation`, `SelfTrainingClassifier` in `sklearn.semi_supervised`.
- **Likelihood vs probability**: the PDF is a function of x with θ fixed; likelihood is a function of θ with x fixed and doesn't integrate to 1. **MLE/MAP** maximize (log) likelihood (× prior).
- **BIC = log(m)p − 2log(L̂)**; **AIC = 2p − 2log(L̂)**.
- **Other clusterers**: agglomerative (hierarchy, connectivity matrix, scales with sparse kNN graphs), BIRCH (huge data, < 20 features), mean-shift (finds k, O(m²)), affinity propagation (exemplars, O(m²)), spectral (similarity-matrix embedding, complex structures, poor scaling).
- **Other anomaly detectors**: **Fast-MCD** (`EllipticEnvelope`, single Gaussian, cleaning), **Isolation Forest** (random splits isolate anomalies in fewer steps; good in high-D), **LOF** (local density vs neighbors), **One-class SVM** (novelty; poor scaling), **PCA reconstruction error**.

## Mental Models
- Think of **k-means as a spherical-blob detector**: it fails on ellipsoids, varying sizes/densities, and nonconvex shapes. **Scale features first**.
- Use **GMMs for ellipsoidal clusters and density**; they fail on nonellipsoidal shapes (moons give 8 ellipses instead of 2).
- **Label representatives, not random samples**: 50 well-chosen labels outperform 50 random ones by 10 points.
- **Density threshold = business trade-off**: set the percentile from the acceptable defect rate (e.g. 2%); lower it for fewer false positives, raise it for fewer false negatives.
- **If outliers corrupt "normality"**: fit, drop the worst outliers, refit, or use robust covariance (`EllipticEnvelope`).

## Anti-patterns
- **Picking k from the inertia elbow alone**: it suggested 4 when the true value was 5; check silhouettes.
- **GMM with default `n_init=1`**: EM converges to poor solutions; set `n_init=10`.
- **Trusting DBSCAN with a tiny `eps`**: many anomalies and fragmented clusters (eps 0.05 → 7 clusters; 0.2 → the right 2).
- **Using inertia/silhouette for GMM selection**: unreliable for nonspherical clusters; use BIC/AIC.
- **Running k-means on unscaled data**.

## Code Examples
```python
from sklearn.cluster import KMeans
k = 50
kmeans = KMeans(n_clusters=k, random_state=42)
X_digits_dist = kmeans.fit_transform(X_train)            # distances to centroids
representative_digit_idx = np.argmin(X_digits_dist, axis=0)
X_representative_digits = X_train[representative_digit_idx]
y_representative_digits = np.array([...])                # label these 50 by hand

y_train_propagated = np.empty(len(X_train), dtype=np.int64)
for i in range(k):
    y_train_propagated[kmeans.labels_ == i] = y_representative_digits[i]

percentile_closest = 99
X_cluster_dist = X_digits_dist[np.arange(len(X_train)), kmeans.labels_]
for i in range(k):
    in_cluster = (kmeans.labels_ == i)
    cutoff = np.percentile(X_cluster_dist[in_cluster], percentile_closest)
    X_cluster_dist[in_cluster & (X_cluster_dist > cutoff)] = -1
partially_propagated = (X_cluster_dist != -1)
```
- **What it demonstrates**: the semi-supervised recipe: representatives, then propagation, then dropping outliers.

```python
gm = GaussianMixture(n_components=3, n_init=10).fit(X)
densities = gm.score_samples(X)
anomalies = X[densities < np.percentile(densities, 2)]     # 2% threshold
gm.bic(X), gm.aic(X)
bgm = BayesianGaussianMixture(n_components=10, n_init=10, random_state=42).fit(X)
bgm.weights_.round(2)    # [0.4, 0.21, 0.4, 0, 0, ...] → 3 clusters
```

## Reference Tables
| Algorithm | Cluster shape | Needs k | Scales | Predicts new | Anomalies |
|---|---|---|---|---|---|
| k-means / MiniBatch | Spherical, similar size | Yes | Very well | Yes | Via distance |
| DBSCAN / HDBSCAN | Any; uniform density | No (eps, min_samples) | O(m log m)–O(m²) | No (use kNN) | Yes (−1) |
| GMM | Ellipsoidal | Yes (BIC/AIC) | Depends on covariance_type | Yes, soft | Yes (density) |
| Bayesian GMM | Ellipsoidal | Upper bound only | Like GMM | Yes | Yes |
| Agglomerative | Any (hierarchical) | Optional | With connectivity | No | No |
| Spectral | Complex | Yes | Poor | No | No |

| Semi-supervised digits (50 labels) | Test accuracy |
|---|---|
| 50 random labeled instances | 74.8% |
| 50 representative instances | 84.9% |
| Propagate to all instances | 89.4% |
| Propagate, drop farthest 1% | **90.9%** (full labels: 90.7%) |

## Worked Example
**Choosing k on 5 blobs**: inertia drops fast to k = 4 and then slowly (elbow at 4, but wrong). Silhouette scores peak at k = 4 and k = 5 is nearly as good; the silhouette diagram for k = 5 shows all clusters similar in size and beyond the mean line, so **choose 5**. Score for kmeans k = 5: 0.655.

**DBSCAN on moons**: `DBSCAN(eps=0.05, min_samples=5)` gives 7 clusters and many −1s. With `eps=0.2` it finds the 2 moons. Then train `KNeighborsClassifier(n_neighbors=50)` on `dbscan.components_` for prediction, and flag a new point as an anomaly if its nearest core is > 0.2 away.

## Key Takeaways
1. Scale features; use k-means++ with multiple inits; choose k with silhouette diagrams.
2. Use clustering as features (`ClusterSimilarity`), for dimensionality reduction (`transform`), and for semi-supervised labeling.
3. Label representative instances and propagate, then iterate with active learning.
4. Use DBSCAN/HDBSCAN for arbitrary shapes and outlier robustness; GMMs for ellipsoids, densities and generation.
5. Pick GMM k with BIC/AIC or a `BayesianGaussianMixture`.
6. Anomaly detection: GMM density percentile, Isolation Forest (high-D), LOF, EllipticEnvelope; novelty: One-class SVM.

## Connects To
- **Ch 2**: `ClusterSimilarity` features with KMeans.
- **Ch 8**: dimensionality reduction and PCA reconstruction-error anomalies.
- **Ch 14**: semantic/instance segmentation with CNNs.
- **Ch 17**: autoencoders for anomaly detection; generative models.
