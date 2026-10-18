# Chapter 14: Deep Computer Vision Using Convolutional Neural Networks

## Core Idea
CNNs, inspired by the visual cortex's **local receptive fields**, use **convolutional layers** (shared filters producing feature maps) and **pooling layers** to build hierarchical features with far fewer parameters than dense nets. The chapter traces architectures from LeNet-5 to AlexNet, GoogLeNet, VGG, ResNet, Xception, SENet and EfficientNet. In practice you **reuse pretrained models** (`tf.keras.applications`) via transfer learning, and extend CNNs to **localization, object detection (FCN, YOLO), tracking (DeepSORT), and semantic/instance segmentation**.

## Frameworks Introduced
- **Convolutional layer**: each neuron connects only to an f_h × f_w receptive field; all neurons in a feature map share one filter (+ bias). Output is one feature map per filter. **Stride** downsamples; **padding** `"valid"` (no padding) vs `"same"` (output = ⌈input/stride⌉).
- **Translation invariance via weight sharing**: a pattern learned anywhere is recognized everywhere; a dense net only recognizes it where it learned it.
- **Pooling**: max pooling (default 2×2, stride 2) shrinks compute, memory and params and adds small translation invariance, but drops 75% of activations. **Global average pooling** outputs one value per feature map (used before the final dense layer). **Depthwise pooling** pools across channels (learns invariance to rotation, thickness, etc.).
- **Typical CNN pattern**: [Conv-ReLU] × k → Pool, repeated, with **filters doubling** (64 → 128 → 256) as spatial size halves, then Flatten/GAP → Dense → Dropout → softmax.
- **Small kernels rule**: instead of one 5×5, **stack two 3×3** (fewer params, less compute, usually better). Exception: the first layer may use a large kernel (e.g. 7×7, stride 2) to cut spatial size early.
- **Architecture lineage** (ILSVRC top-5 error):
  - *LeNet-5* (1998, MNIST).
  - *AlexNet* (2012, 17%): stacked convs, dropout 50%, data augmentation, LRN.
  - *GoogLeNet* (2014, < 7%): **inception modules** with **1×1 bottleneck convs** (capture cross-channel patterns, reduce dims, pair into stronger convs), GAP.
  - *VGGNet*: simple 3×3 stacks.
  - *ResNet* (2015, < 3.6%, 152 layers): **residual learning** with skip connections. The net models f(x) = h(x) − x, starts near identity, and signals flow through the skip paths. A 1×1 stride-2 conv on the skip when shape changes; bottleneck units (1×1 → 3×3 → 1×1) for deep variants.
  - *Xception* (Chollet): **depthwise separable convolutions** (spatial per channel, then 1×1 across channels).
  - *SENet* (2017, 2.25%): **squeeze-and-excitation block** (GAP → Dense ReLU (squeeze, e.g. 1/16) → Dense sigmoid → rescale feature maps).
  - Also: ResNeXt, DenseNet, MobileNet, CSPNet, **EfficientNet** (compound scaling of depth α^ϕ, width β^ϕ, resolution γ^ϕ).
- **Choosing an architecture**: trade accuracy vs size vs CPU/GPU latency (Table 14-3). MobileNet for mobile; EfficientNet B0–B7 for accuracy/size balance.
- **Transfer learning for images**:
  1. Load the base with `include_top=False` and add GAP + Dense(softmax).
  2. Freeze the base layers (individually), train the head (high LR).
  3. Unfreeze the top layers (e.g. `base_model.layers[56:]`), recompile with a lower LR (0.1 → 0.01), train more. Flowers: ~92% test accuracy in minutes, 95–97% with tuning.
- **Object detection progression**: sliding CNN (slow) → **fully convolutional network (FCN)** (replace dense layers with equivalent convs, so any input size works and the CNN slides in a single pass) → **YOLO** (per grid cell: boxes with objectness, cell-relative coordinates, anchor priors in v2+) → also SSD, Faster R-CNN, EfficientDet.
- **Non-max suppression (NMS)**: drop boxes below an objectness threshold, keep the highest, remove overlapping boxes (IoU > ~60%), repeat.
- **DeepSORT tracking**: Kalman filter (constant-velocity prior) + deep appearance similarity + Hungarian assignment.
- **Semantic segmentation (FCN, Long et al.)**: downsample, then upsample with **transposed convolutions**, with **skip connections** from lower layers to recover resolution (×32 → ×2 + skips). Instance segmentation: **Mask R-CNN**.

## Key Concepts
- **Feature map**: output of one filter; **kernel shape** [f_h, f_w, in_channels, out_channels] doesn't depend on image size.
- **Input tensors**: [batch, height, width, channels].
- **Output size**: valid → ⌊(i − f + s)/s⌋; same → ⌈i/s⌉.
- **Memory**: the backward pass stores forward activations. For OOM: reduce batch size, use stride, remove layers, use float16, or distribute.
- **Data augmentation**: realistic variants (shift, rotate, flip, contrast, lighting); a regularizer; for imbalance cf. **SMOTE**. In Keras: `RandomFlip`, `RandomRotation`, `RandomContrast` layers (training only).
- **1×1 convolution**: per-pixel dense layer across channels (bottleneck).
- **Localization**: add a Dense(4) regression head (center x, y, √h, √w normalized to 0–1); `loss=["sparse_categorical_crossentropy", "mse"]` with loss weights. Evaluate with **IoU** (`MeanIoU`).
- **mAP (mean average precision)**: average of max precision at recall ≥ 0, 0.1, …, 1 (AP), averaged over classes; a detection counts only if IoU > threshold (mAP@0.5 for PASCAL; COCO averages IoU 0.5–0.95).
- **Dilated (à-trous) convolution**: `dilation_rate` for a larger receptive field at no extra cost. `Conv1D` for sequences, `Conv3D` for volumes.

## Mental Models
- Think of a CNN as **zooming out**: early layers see edges, middle layers see parts, top layers see objects. Spatial size shrinks while depth (features) grows.
- **ResNet as a highway system**: skip connections let gradients and signals bypass layers that haven't learned anything yet, so training makes progress even when some layers are stuck.
- **SE block as attention over channels**: "eyes and nose fire together, so boost the mouth too".
- **FCN trick**: a Dense layer on a 7×7×100 map equals a Conv2D(200, kernel 7, valid). After conversion, a bigger image gives a grid of predictions in one pass.
- **Labels are the expensive part**: budget for annotation tools (VGG Image Annotator, LabelImg, CVAT…) or crowdsourcing.

## Anti-patterns
- **Fully connected nets for large images**: 100×100 images with 1,000 neurons means 10M params in the first layer alone.
- **Large kernels everywhere**.
- **`base_model.trainable=False` when the model uses the base layers directly**: no effect; freeze each layer.
- **Forgetting `preprocess_input`** for the specific pretrained model, or the wrong input size.
- **Separable convs right after the input** (few channels): use regular convs there.
- **Training on CPU in Colab** (minutes per epoch vs seconds on GPU).

## Code Examples
```python
DefaultConv2D = partial(tf.keras.layers.Conv2D, kernel_size=3, padding="same",
                        activation="relu", kernel_initializer="he_normal")
model = tf.keras.Sequential([
    DefaultConv2D(filters=64, kernel_size=7, input_shape=[28, 28, 1]),
    tf.keras.layers.MaxPool2D(),
    DefaultConv2D(filters=128), DefaultConv2D(filters=128),
    tf.keras.layers.MaxPool2D(),
    DefaultConv2D(filters=256), DefaultConv2D(filters=256),
    tf.keras.layers.MaxPool2D(),
    tf.keras.layers.Flatten(),
    tf.keras.layers.Dense(128, activation="relu", kernel_initializer="he_normal"),
    tf.keras.layers.Dropout(0.5),
    tf.keras.layers.Dense(64, activation="relu", kernel_initializer="he_normal"),
    tf.keras.layers.Dropout(0.5),
    tf.keras.layers.Dense(10, activation="softmax")])     # >92% on Fashion MNIST
```

```python
class ResidualUnit(tf.keras.layers.Layer):
    def __init__(self, filters, strides=1, activation="relu", **kwargs):
        super().__init__(**kwargs)
        self.activation = tf.keras.activations.get(activation)
        self.main_layers = [
            DefaultConv2D(filters, strides=strides),     # use_bias=False, no activation
            tf.keras.layers.BatchNormalization(), self.activation,
            DefaultConv2D(filters), tf.keras.layers.BatchNormalization()]
        self.skip_layers = []
        if strides > 1:
            self.skip_layers = [DefaultConv2D(filters, kernel_size=1, strides=strides),
                                tf.keras.layers.BatchNormalization()]

    def call(self, inputs):
        Z = inputs
        for layer in self.main_layers:
            Z = layer(Z)
        skip_Z = inputs
        for layer in self.skip_layers:
            skip_Z = layer(skip_Z)
        return self.activation(Z + skip_Z)
# ResNet-34: filters [64]*3 + [128]*4 + [256]*6 + [512]*3, stride 2 when filters change
```

```python
base_model = tf.keras.applications.xception.Xception(weights="imagenet", include_top=False)
avg = tf.keras.layers.GlobalAveragePooling2D()(base_model.output)
output = tf.keras.layers.Dense(n_classes, activation="softmax")(avg)
model = tf.keras.Model(inputs=base_model.input, outputs=output)
for layer in base_model.layers:
    layer.trainable = False
model.compile(loss="sparse_categorical_crossentropy",
              optimizer=tf.keras.optimizers.SGD(learning_rate=0.1, momentum=0.9),
              metrics=["accuracy"])
model.fit(train_set, validation_data=valid_set, epochs=3)
for layer in base_model.layers[56:]:
    layer.trainable = True
model.compile(loss="sparse_categorical_crossentropy",
              optimizer=tf.keras.optimizers.SGD(learning_rate=0.01, momentum=0.9),
              metrics=["accuracy"])
model.fit(train_set, validation_data=valid_set, epochs=10)
```

## Reference Tables
| Pretrained (Keras) | Size MB | Top-1 | Top-5 | Params |
|---|---|---|---|---|
| MobileNetV2 | 14 | 71.3% | 90.1% | 3.5M |
| EfficientNetB0 | 29 | 77.1% | 93.3% | 5.3M |
| EfficientNetB3 | 48 | 81.6% | 95.7% | 12.3M |
| InceptionV3 | 92 | 77.9% | 93.7% | 23.9M |
| ResNet50V2 | 98 | 76.0% | 93.0% | 25.6M |
| InceptionResNetV2 | 215 | 80.3% | 95.3% | 55.9M |
| EfficientNetB7 | 256 | 84.3% | 97.0% | 66.7M |

| Vision task | Output | Approach |
|---|---|---|
| Classification | class probs | CNN + GAP + softmax |
| Classification + localization | class + 4 box coords | 2 heads; MSE train, IoU eval |
| Object detection | many boxes + classes | FCN / YOLO / SSD / Faster R-CNN + NMS; mAP |
| Tracking | identities over frames | DeepSORT |
| Semantic segmentation | class per pixel | FCN + transposed conv + skips |
| Instance segmentation | mask per object | Mask R-CNN |

## Worked Example
**Shapes in a conv layer**: 2 sample images center-cropped to 70×120×3 → `Conv2D(32, kernel_size=7)` (valid) gives **[2, 64, 114, 32]** (70 − 7 + 1 = 64; 120 − 7 + 1 = 114). With `padding="same"` it's [2, 70, 120, 32]; with `strides=2, padding="same"` it's [2, 35, 60, 32]. Kernels have shape (7, 7, 3, 32) and biases (32,): 4,736 params regardless of image size. A dense layer would need millions.

**Pretrained ResNet-50 inference**: `Resizing(224, 224, crop_to_aspect_ratio=True)` → `resnet50.preprocess_input` → `predict` gives (2, 1000) → `decode_predictions(top=3)`: palace 54.7% (correct); vase 32.7% for a dahlia, which isn't in ImageNet's 1,000 classes, so use transfer learning for custom classes.

## Key Takeaways
1. Use conv + pooling stacks with 3×3 kernels, doubling filters as resolution halves; GAP before the head.
2. Don't build from scratch: pick a pretrained model by accuracy/size/latency and fine-tune (freeze, train head, unfreeze top, lower LR, recompile).
3. Always apply the model-specific `preprocess_input` and input size; augment small datasets.
4. ResNet skip connections and BN make very deep nets trainable; SE blocks and separable convs improve efficiency.
5. Detection = FCN/YOLO + NMS, evaluated by mAP; localization uses IoU; segmentation uses transposed convs + skips.
6. When out of memory: smaller batch, strides, fewer layers, float16, or distribute.

## Connects To
- **Ch 11**: transfer learning, BN, He init, dropout.
- **Ch 13**: image preprocessing/augmentation layers, TFDS.
- **Ch 15**: Conv1D and WaveNet (dilated convs) for sequences.
- **Ch 16**: vision transformers (ViT, DeiT).
- **Ch 17**: transposed convs in autoencoders/GANs; U-Net in diffusion.
- **Ch 19**: deploying on mobile (MobileNet, TFLite).
