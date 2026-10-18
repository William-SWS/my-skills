# Chapter 8: Dimensionality Reduction

## Core Idea
High-dimensional data is sparse and slow to train on (the **curse of dimensionality**). Real data usually lies near a lower-dimensional subspace (use **projection**: PCA, random projection) or a twisted **manifold** (use **manifold learning**: LLE, Isomap, t-SNE). **Train on the original data first**: reduction loses information and complicates pipelines. Use it for speed, compression, noise filtering, or visualization.

## Frameworks Introduced
- **Curse of dimensionality**: in a 10,000-D unit hypercube, nearly every point is near a border (>99.999999%); the average distance between two random points is ~40.8 in 1,000,000-D. Training sets are sparse, so predictions are extrapolations and overfitting risk rises. The data needed to keep density constant grows exponentially with dimensions.
- **Projection vs manifold learning**:
  - *Projection*: when instances lie close to a hyperplane (correlated/near-constant features). Fails on twisted shapes (squashes Swiss roll layers).
  - *Manifold hypothesis*: real high-D data lies close to a much lower-D manifold (e.g. MNIST digits). Implicit assumption: the task is simpler in the manifold, which **isn't always true**.
- **PCA = preserve maximum variance**: choose the axis with maximum variance (equivalently, minimum mean squared projection distance), then orthogonal axes for the remaining variance. Components come from SVD: X = UΣVᵀ, and the PCs are the columns of V.
- **Choosing d**: smallest d reaching **95% explained variance** (`PCA(n_components=0.95)`); or the elbow of the cumulative variance plot; or **tune d as a hyperparameter** inside a supervised pipeline. For visualization, d = 2 or 3.
- **Scaling PCA**: Randomized PCA (`svd_solver="randomized"`, auto when max(m,n) > 500 and d < 80% of min(m,n)); **Incremental PCA** (`partial_fit` on mini-batches or `np.memmap`) for out-of-core/online; **Random projection** when n is in the tens of thousands or more.
- **Johnson–Lindenstrauss lemma**: random projection to d ≥ 4 log(m)/(½ε² − ⅓ε³) dimensions preserves pairwise distances within ±ε with high probability (m = 5,000, ε = 0.1 → d = 7,300). It doesn't depend on n.

## Key Concepts
- **Explained variance ratio** (`explained_variance_ratio_`): fraction of variance per PC.
- **`components_`**: rows are PCs (Wdᵀ). PC directions are unstable in sign but the axes are stable.
- **Reconstruction error**: mean squared distance between original and `inverse_transform` data. X_recovered = X_d-proj Wdᵀ.
- **PCA for compression**: MNIST 784 → 154 features (95% variance), under 20% of the size, digits still legible.
- **`GaussianRandomProjection` / `SparseRandomProjection`**: the sparse version is much faster and lighter (density 1/√n by default); prefer it.
- **LLE (Locally Linear Embedding)**: reconstruct each point linearly from its k nearest neighbors, then find a low-D embedding preserving those weights. Good for unrolling twisted manifolds with little noise; scales poorly (O(dm²)).
- **MDS**: preserve distances. **Isomap**: preserve geodesic distances on a kNN graph. **t-SNE**: keep similar instances close, mostly for visualizing clusters. **LDA**: learn the most discriminative axes between classes; good before another classifier.
- **Fruit fly olfaction ≈ random projection / LSH**: dense low-D inputs map to sparse high-D outputs.

## Mental Models
- Think of PCA as **choosing the best camera angle** to photograph a 3D point cloud so it looks maximally spread out.
- **PCA assumes centered data**: Scikit-Learn centers for you; manual SVD needs `X - X.mean(axis=0)`.
- **Powerful downstream model means fewer dimensions needed**: RF + PCA tuned to only **23 components** on MNIST; a linear model would need more.
- **Random projection is data-agnostic**: only the shape is needed, and no training. Great as a first step for huge n.
- Pick the method by goal: **speed/compression → PCA family; huge n → random projection; visualization → t-SNE (or PCA/UMAP-like); unrolling manifolds → LLE/Isomap; class separation → LDA**.

## Anti-patterns
- **Reducing dimensionality before trying the raw data**: you may lose performance for nothing.
- **Assuming the reduced space makes the task simpler**: Fig 8-6 shows a boundary that is simple in 3D (x₁ = 5) and complex in the unrolled manifold.
- **Forgetting shape/dtype with `np.memmap`**: you get a 1D array.
- **Inverting a big random projection casually**: `pinv` is O(dn²).
- **Using t-SNE output as model features**: it's for visualization, and it doesn't preserve global structure.

## Code Examples
```python
from sklearn.decomposition import PCA, IncrementalPCA
pca = PCA(n_components=0.95)                 # keep 95% of variance
X_reduced = pca.fit_transform(X_train)       # pca.n_components_ == 154
X_recovered = pca.inverse_transform(X_reduced)

inc_pca = IncrementalPCA(n_components=154)   # out-of-core
for X_batch in np.array_split(X_train, 100):
    inc_pca.partial_fit(X_batch)

clf = make_pipeline(PCA(random_state=42), RandomForestClassifier(random_state=42))
param_distrib = {"pca__n_components": np.arange(10, 80),
                 "randomforestclassifier__n_estimators": np.arange(50, 500)}
rnd_search = RandomizedSearchCV(clf, param_distrib, n_iter=10, cv=3, random_state=42)
rnd_search.fit(X_train[:1000], y_train[:1000])   # best: 23 components, 465 trees

from sklearn.random_projection import johnson_lindenstrauss_min_dim, SparseRandomProjection
d = johnson_lindenstrauss_min_dim(5_000, eps=0.1)   # 7300
X_rp = SparseRandomProjection(eps=0.1, random_state=42).fit_transform(X)

from sklearn.manifold import LocallyLinearEmbedding
X_unrolled = LocallyLinearEmbedding(n_components=2, n_neighbors=10,
                                    random_state=42).fit_transform(X_swiss)
```
- **What it demonstrates**: variance-targeted PCA, out-of-core PCA, tuning d inside a pipeline, JL-sized random projection, LLE.

## Reference Tables
| Method | Type | Complexity / scale | Best for |
|---|---|---|---|
| PCA (full SVD) | Linear projection | O(m n²) + O(n³) | Default; compression; speed-up |
| Randomized PCA | Linear | O(m d²) + O(d³) | d ≪ n |
| Incremental PCA | Linear | Mini-batches | Out-of-core / online |
| Gaussian/Sparse Random Projection | Linear, random | No training; sparse is fastest | n ≥ 10⁴ features |
| LLE | Manifold | O(d m²): poor for large m | Unrolling twisted manifolds |
| MDS | Distance-preserving | – | Low-D data, global structure |
| Isomap | Geodesic | – | Manifolds (drops global curvature) |
| t-SNE | Neighborhood | Slow | Visualization of clusters |
| LDA | Supervised linear | – | Preprocessing for classifiers |

## Worked Example
**Choosing d on MNIST**:
1. `PCA().fit(X_train)`; `cumsum = np.cumsum(pca.explained_variance_ratio_)`.
2. `d = np.argmax(cumsum >= 0.95) + 1` gives **154** (from 784). Equivalent: `PCA(n_components=0.95)`.
3. Cumulative-variance plot: the elbow is near 100 dims, so reducing to ~100 loses little.
4. Compression check: `inverse_transform` gives digits with a slight quality loss but intact.
5. For classification, tune instead: RF pipeline best at **23 components**, showing that the right d depends on the downstream model, not just the variance.

## Key Takeaways
1. Try the original features first; reduce only for speed, memory, visualization, or noise.
2. PCA with `n_components=0.95` is the default starting point; treat d as a hyperparameter for supervised tasks.
3. Use randomized/incremental PCA for big data, and (sparse) random projection for very high n.
4. Manifold learners (LLE, Isomap, t-SNE) handle twisted structure but scale poorly and are mostly for exploration/visualization.
5. Always fit the reducer on the training set only, inside the pipeline.

## Connects To
- **Ch 1**: dimensionality reduction as an unsupervised preprocessing step.
- **Ch 4**: SVD behind `LinearRegression`.
- **Ch 6**: PCA rotation for decision trees.
- **Ch 9**: clustering as dimensionality reduction (cluster affinities).
- **Ch 17**: autoencoders (nonlinear PCA).
