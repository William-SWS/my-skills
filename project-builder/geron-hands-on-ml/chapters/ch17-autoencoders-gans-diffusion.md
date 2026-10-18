# Chapter 17: Autoencoders, GANs, and Diffusion Models

## Core Idea
Three families learn data distributions without labels. **Autoencoders** learn compressed **latent codings** by reconstructing their inputs under constraints (undercomplete, denoising, sparse, variational); they're used for dimensionality reduction, pretraining, anomaly detection and generation. **GANs** pit a **generator** against a **discriminator** in a zero-sum game, producing sharp images but training unstably (DCGAN, ProGAN, StyleGAN). **Diffusion models (DDPM)** learn to remove a little noise at a time; they're slow to sample but high-quality and diverse, and latent diffusion powers Stable Diffusion.

## Frameworks Introduced
- **Autoencoder = encoder (recognition network) + decoder (generative network)**, trained with inputs as targets (a form of self-supervised learning). **Undercomplete** (coding dim < input dim) forces it to learn the most important patterns (like chess masters remembering *realistic* positions).
- **Linear AE + MSE = PCA** (Dense(2) encoder, Dense(3) decoder, no activations).
- **Stacked (deep) AE**: symmetric, e.g. 784 → 100 → **30** → 100 → 784. Too powerful an AE memorizes (maps each input to an arbitrary number) and learns nothing useful.
- **Uses of AEs**: visualization (AE → 30D, then t-SNE → 2D, which scales to big data), **unsupervised pretraining** (train on all data, reuse the encoder for a small labeled task), anomaly detection (reconstruction error), generation (VAE).
- **Training tricks**: **tied weights** (decoder uses the transposed encoder weights, `DenseTranspose`, halving params); **greedy layer-wise training** (one shallow AE at a time; historical).
- **Convolutional AE**: Conv2D + pooling encoder; `Conv2DTranspose` decoder.
- **Regularized (overcomplete-capable) AEs**:
  - *Denoising*: add Gaussian noise or **dropout** to the inputs and reconstruct clean inputs.
  - *Sparse*: large sigmoid coding layer (300) + ℓ1 activity regularization (`ActivityRegularization(l1=1e-4)`), or a **KL-divergence** sparsity loss toward a target activation p (e.g. 0.1; weight 5e-3).
  - *Variational (VAE, Kingma & Welling 2013)*: **probabilistic and generative**. The encoder outputs μ and γ = log σ²; **sampling** z = μ + exp(γ/2)·ε (reparameterization). Loss = reconstruction + **latent loss** −½Σ(1 + γ − exp(γ) − μ²) (KL to N(0, I)). Supports **semantic interpolation** in latent space.
- **GAN (Goodfellow 2014)**, two-phase training per iteration:
  1. Train the **discriminator** on real (label 1) + fake (label 0) images.
  2. Train the **generator** through the frozen discriminator on fakes labeled **1** (trying to fool it).
  - The generator never sees real images, only gradients through the discriminator.
- **GAN training difficulties**: the target is a **Nash equilibrium** that may never be reached. **Mode collapse** (the generator produces one convincing class, the discriminator adapts, it switches class…); oscillation/instability; sensitivity to hyperparameters.
  - Remedies: **experience replay** (train D on past fakes too), **mini-batch discrimination** (D measures diversity across a batch), spectral normalization, Wasserstein loss, careful architectures.
- **DCGAN guidelines** (Radford 2015):
  - Replace pooling with strided convs (D) and transposed convs (G).
  - BN in both, except the G output and D input layers.
  - Remove fully connected hidden layers in deeper nets.
  - G uses ReLU (tanh output, so scale data to −1..1); D uses LeakyReLU.
- **Conditional GAN**: feed the class label to both nets to control generation.
- **Progressive Growing of GANs (Nvidia 2018)**: start at 4×4 and add layers up to high-res, with fade-in. Adds a *mini-batch std-dev layer* (diversity), *equalized learning rate* (N(0,1) init scaled at runtime by the He factor), and *pixelwise normalization* in G.
- **StyleGAN**: **mapping network** (8-layer MLP, z → w) controls styles via **AdaIN** at each scale of a **synthesis network** that starts from a learned constant; per-layer **noise inputs** for stochastic detail (freckles, hair); **style mixing regularization** (switch codings mid-network).
- **Diffusion (DDPM, Ho et al. 2020)**:
  - *Forward process*: add Gaussian noise over T steps with a **cosine variance schedule** βₜ; shortcut xₜ = √ᾱₜ·x₀ + √(1 − ᾱₜ)·ε.
  - *Training*: sample a random t, noise the image, and train the model to **predict the noise ε** (better than predicting x₀). Loss MAE/Huber.
  - *Sampling*: start from pure noise and apply the reverse step T times (slow).
  - Architecture: **U-Net** (downsample/upsample with skip connections) + **sinusoidal time encodings** + attention.
  - **Latent diffusion** (Rombach 2021): diffuse in an autoencoder's latent space, much faster. With CLIP text conditioning it becomes **Stable Diffusion** (in KerasCV).

## Key Concepts
- **Codings / latent representation / latent space**.
- **Reconstruction loss**: MSE (or binary cross-entropy for [0,1] pixels).
- **KL divergence** D_KL(P‖Q) = Σ P log(P/Q); for sparsity: p log(p/q) + (1 − p) log((1 − p)/(1 − q)).
- **Reparameterization trick**: sample ε ~ N(0, I) so gradients flow through μ and σ.
- **`discriminator.trainable = False` before compiling `gan`**: the trainable flag is read at compile time, so D still trains through its own `train_on_batch`.
- **`train_on_batch`** for custom GAN loops; `drop_remainder=True` keeps batch sizes fixed.
- **Evaluating GANs**: hard. Use human raters, or **FID** / Inception score (diversity + quality); visual inspection is subjective.
- **Generative vs discriminative**: generative models can sample new data (VAE, GAN, DDPM, GMM).

## Mental Models
- Think of the **AE bottleneck as forcing a summary**: like memorizing "even numbers from 50 to 14" instead of 19 digits.
- Think of a **GAN as counterfeiter vs police**: both improve until fakes are indistinguishable, or they oscillate forever.
- Think of **diffusion as learning to un-drown an image in tiny steps**: each step is an easy denoising task, so it trains stably, and sampling is just many easy steps.
- **Speed/quality/diversity triangle**: VAEs are fast but blurry; GANs fast and sharp but mode-collapse-prone; diffusion is slow but sharp and diverse (latent diffusion speeds it up).

## Anti-patterns
- **An AE that's too powerful or too wide without regularization**: perfect reconstruction, useless codings.
- **Training a GAN with `fit()`**: you need the alternating two-phase loop.
- **Forgetting to freeze D before compiling the combined GAN**, or forgetting to rescale data to −1..1 for a tanh generator.
- **Trusting a single GAN run**: changing the random seed sometimes fixes training.
- **Predicting x₀ instead of the noise** in DDPM.
- **Expecting fast sampling from pixel-space diffusion** (4,000 model calls).

## Code Examples
```python
class Sampling(tf.keras.layers.Layer):
    def call(self, inputs):
        mean, log_var = inputs
        return tf.random.normal(tf.shape(log_var)) * tf.exp(log_var / 2) + mean

codings_size = 10
inputs = tf.keras.layers.Input(shape=[28, 28])
Z = tf.keras.layers.Flatten()(inputs)
Z = tf.keras.layers.Dense(150, activation="relu")(Z)
Z = tf.keras.layers.Dense(100, activation="relu")(Z)
codings_mean = tf.keras.layers.Dense(codings_size)(Z)        # μ
codings_log_var = tf.keras.layers.Dense(codings_size)(Z)     # γ
codings = Sampling()([codings_mean, codings_log_var])
variational_encoder = tf.keras.Model(inputs=[inputs],
                                     outputs=[codings_mean, codings_log_var, codings])
# decoder: 10 → 100 → 150 → 784 → Reshape([28, 28])
_, _, codings = variational_encoder(inputs)
reconstructions = variational_decoder(codings)
variational_ae = tf.keras.Model(inputs=[inputs], outputs=[reconstructions])
latent_loss = -0.5 * tf.reduce_sum(
    1 + codings_log_var - tf.exp(codings_log_var) - tf.square(codings_mean), axis=-1)
variational_ae.add_loss(tf.reduce_mean(latent_loss) / 784.)
variational_ae.compile(loss="mse", optimizer="nadam")
```

```python
discriminator.compile(loss="binary_crossentropy", optimizer="rmsprop")
discriminator.trainable = False
gan = tf.keras.Sequential([generator, discriminator])
gan.compile(loss="binary_crossentropy", optimizer="rmsprop")

def train_gan(gan, dataset, batch_size, codings_size, n_epochs):
    generator, discriminator = gan.layers
    for epoch in range(n_epochs):
        for X_batch in dataset:
            # phase 1 - train the discriminator
            noise = tf.random.normal(shape=[batch_size, codings_size])
            generated_images = generator(noise)
            X_fake_and_real = tf.concat([generated_images, X_batch], axis=0)
            y1 = tf.constant([[0.]] * batch_size + [[1.]] * batch_size)
            discriminator.train_on_batch(X_fake_and_real, y1)
            # phase 2 - train the generator
            noise = tf.random.normal(shape=[batch_size, codings_size])
            y2 = tf.constant([[1.]] * batch_size)
            gan.train_on_batch(noise, y2)
```

```python
def prepare_batch(X):                         # DDPM training batch
    X = tf.cast(X[..., tf.newaxis], tf.float32) * 2 - 1
    X_shape = tf.shape(X)
    t = tf.random.uniform([X_shape[0]], minval=1, maxval=T + 1, dtype=tf.int32)
    alpha_cm = tf.gather(alpha_cumprod, t)
    alpha_cm = tf.reshape(alpha_cm, [X_shape[0]] + [1] * (len(X_shape) - 1))
    noise = tf.random.normal(X_shape)
    return {"X_noisy": alpha_cm ** 0.5 * X + (1 - alpha_cm) ** 0.5 * noise,
            "time": t}, noise                  # target = the noise
```

## Reference Tables
| Autoencoder type | Constraint | Main use |
|---|---|---|
| Undercomplete linear | Small coding, no activation | PCA |
| Stacked / convolutional | Bottleneck | Dim. reduction, pretraining |
| Denoising | Noisy/dropout inputs | Robust features, denoising |
| Sparse (ℓ1 / KL) | Few active coding units | Feature extraction |
| Variational | Latent ~ N(0, I) | Generation, interpolation |

| Generative family | Sample speed | Quality | Diversity | Training stability |
|---|---|---|---|---|
| VAE | Fast | Blurry | Good | Stable |
| GAN (DCGAN/StyleGAN) | Fast | Sharp | Mode collapse risk | Unstable |
| Diffusion (DDPM) | Slow (T steps) | Sharp | High | Stable |
| Latent diffusion | Faster | Sharp | High | Stable |

## Worked Example
**DCGAN for Fashion MNIST**: generator: codings(100) → Dense(7·7·128) → Reshape(7,7,128) → BN → Conv2DTranspose(64, 5, strides=2, same, ReLU) gives 14×14×64 → BN → Conv2DTranspose(1, 5, strides=2, same, **tanh**) gives 28×28×1. Discriminator: Conv2D(64, 5, s=2, LeakyReLU(0.2)) → Dropout(0.4) → Conv2D(128, 5, s=2, LeakyReLU) → Dropout(0.4) → Flatten → Dense(1, sigmoid). Data: `X_train.reshape(-1, 28, 28, 1) * 2. - 1.`. After ~50 epochs it gives convincing items. The plain dense GAN, by contrast, stays noisy after epoch 1 and may "forget" between epochs. Scaled to faces, DCGAN latent arithmetic works: man with glasses − man + woman = woman with glasses.

## Key Takeaways
1. Use autoencoders for unsupervised representation learning: dim. reduction (+ t-SNE), pretraining, denoising, anomaly detection.
2. Constrain AEs (bottleneck, noise, sparsity, KL to a prior); tie weights to halve params.
3. VAEs: encoder outputs μ, log σ²; reparameterize; add latent KL loss (scaled). Sample N(0, I) codings to generate.
4. GANs: alternate D and G steps; freeze D in the combined model; follow DCGAN rules; watch for mode collapse.
5. For SOTA images use diffusion (predict the noise, U-Net + time embeddings), latent diffusion for speed.
6. Evaluate generative models with FID / human judgment, not just loss curves.

## Connects To
- **Ch 8**: PCA = linear AE; dimensionality reduction.
- **Ch 9**: anomaly detection, GMMs as generative models.
- **Ch 11**: unsupervised pretraining, BN, LeakyReLU.
- **Ch 12**: custom layers (Sampling, DenseTranspose), regularizers, custom loops.
- **Ch 14**: transposed convs, U-Net/FCN.
- **Ch 16**: positional/sinusoidal encodings, attention.
