# Chapter 19: Training and Deploying TensorFlow Models at Scale

## Core Idea
To get a model into production: export a versioned **SavedModel** (with preprocessing inside), then serve it with **TF Serving** (REST/gRPC, hot model swaps, auto-batching), on **Vertex AI** (autoscaling endpoints, batch prediction), on **mobile/embedded** (TFLite, quantization) or in the **browser** (TF.js). For faster training: **GPUs** (memory management, device placement, parallel execution), **model vs data parallelism**, the **Distribution Strategies API** (Mirrored, MultiWorkerMirrored, CentralStorage, ParameterServer, TPU), and cloud training and **hyperparameter tuning on Vertex AI**. Fast training means more experiments, which means better models.

## Frameworks Introduced
- **Wrap models in a service**: decouples the model from the app, so you can update or scale it independently, run A/B experiments, and keep consistent versions across clients.
- **SavedModel versioning**: `model.save(Path(model_name) / "0001", save_format="tf")`. Include preprocessing layers so it ingests raw data. Only pure TF ops are allowed (no `tf.py_function`). Inspect with `saved_model_cli show --dir … --tag_set serve --signature_def serving_default`.
- **TF Serving**: C++ server; Docker `tensorflow/serving` (`-p 8500` gRPC, `-p 8501` REST, `-e MODEL_NAME`, `-v` mount). It watches the model dir and **automatically deploys new versions** (answers pending requests with the old version, then swaps). Options: **model warmup** (assets/extra), unload-before-load to save GPU RAM, `--enable_batching` (auto-batch requests on the GPU). Scale with Kubernetes + load balancing.
- **REST vs gRPC**: REST (JSON, simple, universal, verbose: 15 MB of JSON for a 6 MB batch) vs **gRPC** (protobuf `PredictRequest`, HTTP/2, binary, low latency) for large data or latency-sensitive clients.
- **Vertex AI deployment**: GCS bucket → `aiplatform.Model.upload(artifact_uri, serving_container_image_uri)` → `Endpoint.create()` → `endpoint.deploy(min_replica_count, max_replica_count, machine_type, accelerator_type)` (autoscaling on QPS) → `endpoint.predict(instances=...)` → **undeploy and delete when done**. **Batch prediction jobs** (`model.batch_predict` over JSON Lines / TFRecord / CSV / BigQuery / file lists) need no endpoint.
- **GCP auth hygiene**: OAuth for user-delegated access; **service accounts** with minimal roles for apps; never put secrets in bucket names (which are public and globally unique); **set an alarm to turn services off**; GPU quotas.
- **Edge deployment (TFLite)**: `TFLiteConverter.from_saved_model()` gives a FlatBuffer (mmap-able, no copy). It prunes training ops, folds constants and fuses ops (BN folds into the previous layer). **Post-training quantization** (`optimizations=[tf.lite.Optimize.DEFAULT]`): float32 → int8 weights (4× smaller). Full integer quantization of activations needs a representative dataset; **quantization-aware training** recovers accuracy.
- **TF.js in the browser**: offline/intermittent connectivity, lowest latency, **privacy** (data never leaves the device); PWAs; WebGL GPU support; even training in the browser.
- **GPU resource management**: TF grabs all GPU RAM by default. Options: `CUDA_VISIBLE_DEVICES` per process; `set_logical_device_configuration(gpu, [LogicalDeviceConfiguration(memory_limit=2048)])`; `set_memory_growth(gpu, True)` / `TF_FORCE_GPU_ALLOW_GROWTH`; split one GPU into logical devices to test multi-GPU code.
- **Device placement rules**: preprocessing on the CPU, NN ops on the GPU; minimize transfers (limited bandwidth); keep GPU RAM for what's needed in the next steps. Default is `/gpu:0` if a kernel exists (int32 vars go to the CPU); `with tf.device("/cpu:0")`; silent fallback if the device or kernel is missing.
- **Parallel execution**: TF functions run independent ops in parallel (inter-op thread pool on the CPU; intra-op multithreaded kernels; GPU streams).
- **Uses of multiple GPUs without distribution**: train several models in parallel (hyperparameter search), prefetch on the CPU while the GPU trains, a two-tower model on two GPUs, ensemble members per GPU.
- **Model parallelism**: split the model across devices. Hard for dense nets (cross-device communication); easier for partially connected CNNs and layer-per-device deep RNNs (pipelining). Use **Mesh TensorFlow** or **pipeline parallelism (PipeDream, Pathways)**.
- **Data parallelism**: replicate the model; each replica gets a different mini-batch; average the gradients.
  - *Mirrored strategy* (synchronous **AllReduce**, e.g. NCCL; replicas stay identical).
  - *Centralized parameters* (parameter servers): **synchronous** (wait for all; drop the slowest ~10% via **spare replicas**) or **asynchronous** (no waiting, but **stale gradients**: reduce the LR, drop/scale stale gradients, adjust batch size, **warmup** with one replica). Synchronous with a few spares is usually best (Google Brain 2016).
  - *Bandwidth saturation*: speedups are sublinear (NMT 6× on 8 GPUs; Inception 32× on 50; RankBrain 300× on 500). Use dense models, fewer large GPUs, float16 transfers.
- **Distribution Strategies API**: create the model and `compile` inside `strategy.scope()`; `fit` splits batches across replicas (make the batch size divisible by the number of replicas); load the model inside a scope too.
  - `MirroredStrategy()`: single machine, multi-GPU.
  - `MultiWorkerMirroredStrategy()`: cluster via `TF_CONFIG`; all workers must run the same code (including saving); only the chief keeps its outputs.
  - `CentralStorageStrategy`, `ParameterServerStrategy`, `TPUStrategy`.
- **TF cluster**: tasks grouped into jobs (worker, chief, ps, evaluator); `TF_CONFIG = {"cluster": cluster_spec, "task": {"type": "worker", "index": 0}}`; open the firewall ports.
- **Vertex AI custom training**: the same script, but the chief writes to `AIP_MODEL_DIR`, `AIP_CHECKPOINT_DIR`, `AIP_TENSORBOARD_LOG_DIR`; `aiplatform.CustomTrainingJob(...).run(replica_count, accelerator_type, accelerator_count)`; data on GCS (`gs://` paths work in `tf.data`).
- **Vertex AI hyperparameter tuning** (Bayesian optimization): the script takes argparse hyperparameters and reports via `hypertune.report_hyperparameter_tuning_metric`; `HyperparameterTuningJob(metric_spec, parameter_spec=DoubleParameterSpec(scale="log")…, max_trial_count=100, parallel_trial_count=20)`. Alternatives: distributed Keras Tuner (`KERASTUNER_TUNER_ID`, `KERASTUNER_ORACLE_IP`/`PORT`), **AutoML**.

## Key Concepts
- **Metagraph / tag set ("serve") / SignatureDef ("serving_default")**.
- **Servable versions**; **quiescing** old versions.
- **Edge computing** benefits: no connectivity needed, low latency, less server load, privacy.
- **FlatBuffers**: zero-copy serialization used by TFLite.
- **Symmetrical quantization**: map [−max|w|, +max|w|] to [−127, 127].
- **AllReduce**: collective mean across devices (NCCL, hierarchical copy, ring).
- **Spare replicas**; **stale gradients**; **warmup phase**.
- **`tf.data.experimental.prefetch_to_device`**.
- **Siamese network**: two identical towers.

## Mental Models
- Think of **SavedModel + version folder** as the contract between training and serving: drop a new folder in, and TF Serving rolls it out.
- **Iteration speed is a feature**: hours instead of weeks lets you try many more ideas, so invest in GPUs, data pipelines and distribution early.
- **Data parallelism first**: it's simpler and more general; model parallelism only for models that don't fit or have natural splits.
- **Cloud cost discipline**: autoscale with min replicas = 1, delete endpoints/models/buckets after use, and watch regions (price, CO₂, GPU availability).
- **Trust boundaries**: only run notebooks you trust when they authenticate to your cloud account.

## Anti-patterns
- **Embedding the model in every client app**: version drift, hard updates.
- **Preprocessing outside the exported model**: skew in production.
- **`tf.py_function` in a model you want to serve**.
- **REST for large tensors / latency-critical paths**: use gRPC.
- **Letting TF grab all GPU RAM when running multiple programs**.
- **Uneven batch sizes across replicas** (not divisible by the number of GPUs).
- **Only the chief saving in MultiWorkerMirrored**: deadlock; all workers must save (non-chiefs to a temp dir).
- **Forgetting to undeploy endpoints**: ongoing charges.

## Code Examples
```python
model_name, model_version = "my_mnist_model", "0001"
model_path = Path(model_name) / model_version
model.save(model_path, save_format="tf")
# docker run -it --rm -v "/path/to/my_mnist_model:/models/my_mnist_model" \
#   -p 8500:8500 -p 8501:8501 -e MODEL_NAME=my_mnist_model tensorflow/serving

request_json = json.dumps({"signature_name": "serving_default",
                           "instances": X_new.tolist()})
server_url = "http://localhost:8501/v1/models/my_mnist_model:predict"
response = requests.post(server_url, data=request_json)
response.raise_for_status()
y_proba = np.array(response.json()["predictions"])

converter = tf.lite.TFLiteConverter.from_saved_model(str(model_path))
converter.optimizations = [tf.lite.Optimize.DEFAULT]     # post-training quantization
tflite_model = converter.convert()
```

```python
for gpu in tf.config.list_physical_devices("GPU"):
    tf.config.experimental.set_memory_growth(gpu, True)

strategy = tf.distribute.MirroredStrategy()
with strategy.scope():
    model = tf.keras.Sequential([...])
    model.compile([...])
batch_size = 100                       # divisible by number of replicas
model.fit(X_train, y_train, epochs=10, validation_data=(X_valid, y_valid),
          batch_size=batch_size)

# multi-worker: TF_CONFIG set per machine
strategy = tf.distribute.MultiWorkerMirroredStrategy()     # at the start!
resolver = tf.distribute.cluster_resolver.TFConfigClusterResolver()
with strategy.scope():
    model = build_and_compile()
model.fit(...)
if resolver.task_id == 0:
    model.save("my_mnist_multiworker_model", save_format="tf")
else:
    tmpdir = tempfile.mkdtemp()
    model.save(tmpdir, save_format="tf")
    tf.io.gfile.rmtree(tmpdir)
```

## Reference Tables
| Deployment target | Tool | When |
|---|---|---|
| Own servers | TF Serving (Docker/K8s) | Full control, high QPS, auto-batching |
| Managed cloud | Vertex AI endpoint | Autoscaling, no ops |
| Offline large batch | Vertex AI batch prediction | Millions of predictions, no endpoint |
| Mobile / embedded | TFLite (+ quantization) | Offline, latency, battery |
| Browser | TF.js | Privacy, latency, offline PWA |

| Distribution strategy | Topology | Updates |
|---|---|---|
| `MirroredStrategy` | 1 machine, N GPUs | Sync AllReduce |
| `MultiWorkerMirroredStrategy` | Cluster | Sync AllReduce (ring/NCCL) |
| `CentralStorageStrategy` | 1 machine, params on CPU | Sync |
| `ParameterServerStrategy` | Cluster + PS | Async across workers |
| `TPUStrategy` | TPU pods | Sync |

| Problem | Remedy |
|---|---|
| Stale gradients (async) | Lower LR, drop/scale stale, warmup with 1 replica |
| Stragglers (sync) | Spare replicas: ignore the slowest ~10% |
| Bandwidth saturation | Fewer bigger GPUs, dense models, float16 comms, pipeline parallelism |
| GPU OOM across programs | `CUDA_VISIBLE_DEVICES`, memory limit, memory growth |

## Worked Example
**Vertex AI hyperparameter tuning of an MNIST MLP**: the trial script parses `--n_hidden`, `--n_neurons`, `--learning_rate`, `--optimizer`, builds the model inside `MirroredStrategy().scope()`, trains, and reports `max(val_accuracy)` via `hypertune`. Job: learning_rate log-uniform 1e-3..10, n_neurons 1..300, n_hidden 1..10, optimizer {sgd, adam}; 100 trials, 20 in parallel, 2 K80 GPUs each. Best trial #98: **97.74%** accuracy with lr = 0.001, 8 hidden layers × 216 neurons, Adam. Next: retrieve its SavedModel, optionally train more, then deploy. Note the trade-off: more parallel trials finish faster but give the Bayesian optimizer less information per decision.

## Key Takeaways
1. Export versioned SavedModels with preprocessing included; serve with TF Serving or Vertex AI; use gRPC for heavy traffic.
2. Hot-swap versions by adding folders; enable warmup and auto-batching.
3. On the edge: TFLite + quantization; in the browser: TF.js for privacy and latency.
4. Manage GPU RAM explicitly when sharing GPUs; keep preprocessing on the CPU and prefetch.
5. Prefer data parallelism via `tf.distribute` strategies; build/compile inside `strategy.scope()`; batch size divisible by replicas.
6. Use cloud training + Bayesian hyperparameter tuning to scale experiments, and always clean up resources.

## Connects To
- **Ch 2**: launch, monitor, maintain; joblib deployment.
- **Ch 10/12**: SavedModel, callbacks, TF Functions and graphs.
- **Ch 13**: preprocessing layers inside models; `tf.data` with GCS paths.
- **Ch 14**: MobileNet/EfficientNet for edge deployment.
- **App D**: TF graphs and concrete functions behind SavedModels.
