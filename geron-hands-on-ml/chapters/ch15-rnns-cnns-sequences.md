# Chapter 15: Processing Sequences Using RNNs and CNNs

## Core Idea
RNNs process sequences by carrying a hidden state across time steps and are trained by **backpropagation through time (BPTT)**. The chapter forecasts Chicago transit ridership. First establish **baselines (naive seasonal, SARIMA)**, then a linear model, simple/deep/multivariate RNNs, multi-step forecasting (iterative, seq-to-vector, seq-to-seq). Fix **unstable gradients** (layer norm, recurrent dropout) and **short-term memory** (LSTM, GRU, Conv1D, WaveNet). Always check models against regime changes (Covid-19).

## Frameworks Introduced
- **RNN topologies**: sequence-to-sequence (forecast at every step), sequence-to-vector (e.g. sentiment), vector-to-sequence (e.g. captioning), **encoder–decoder** (seq-to-vector, then vector-to-seq; e.g. translation, which beats a single seq-to-seq because the last words can affect the first translated words).
- **Baseline first**: naive forecasting copies the last value, or **the value one season earlier** (here t − 7 for weekly seasonality). Bus MAPE 8.3%, rail 9.0%. Any model must beat this.
- **Time series toolbox**: seasonality (weekly, yearly), trend, **differencing** (removes trend; lag-s differencing removes seasonality, giving a stationary series), autocorrelation, 12-month rolling average.
- **ARMA family**: AR(p) weighted past values + MA(q) weighted past errors; **ARIMA(p, d, q)** adds d rounds of differencing; **SARIMA(p,d,q)(P,D,Q,s)** adds a seasonal component. Model selection by grid search on AIC (or on validation MAE).
- **Evaluate forecasts by rolling origin** (retrain daily, forecast tomorrow, average errors), not a single day. One day: SARIMA 12.9% off vs naive 12.6%; over 3 months SARIMA MAE 32,041 vs naive 42,143.
- **Windowing with `tf.data`**: `window(length, shift=1, drop_remainder=True)` → `flat_map(lambda w: w.batch(length))` → `map(split)`; or `keras.utils.timeseries_dataset_from_array(series, targets, sequence_length, batch_size, shuffle=True)` (shuffle windows, not their contents).
- **Multi-step forecasting options**:
  1. *Iterative*: predict 1 step, append, repeat. Errors accumulate, so use only for a few steps.
  2. *Seq-to-vector* with Dense(14): all 14 at once, no accumulation.
  3. **Seq-to-seq**: predict the next 14 at **every** time step (`return_sequences=True`). More error gradients, which stabilize and speed up training. The model is **causal** (can't see the future), so overlapping targets aren't cheating.
- **Fixing unstable gradients in RNNs**: saturating tanh (ReLU can explode since the same weights are reused each step), small LR, gradient clipping, **layer normalization** (per instance across features, same at train/test; BN works poorly in RNNs), `dropout` (inputs) and `recurrent_dropout` (between steps). **MC dropout** gives forecast error bars.
- **Fixing short-term memory**:
  - **LSTM** (Hochreiter & Schmidhuber 1997): long-term state c, short-term h; **forget gate** f, **input gate** i, **output gate** o (sigmoid) + main layer g (tanh): c(t) = f⊗c(t−1) + i⊗g; h(t) = o⊗tanh(c(t)). TF initializes the forget bias to 1.
  - **GRU** (Cho 2014): one state vector; update gate z merges forget/input; reset gate r; no output gate. Simpler and about as good.
  - **Conv1D front-end**: downsample sequences (stride 2) so recurrent layers detect longer patterns (crop targets accordingly: `Y[:, 3::2]`).
  - **WaveNet** (DeepMind 2016): stacked **causal** Conv1D with dilation 1, 2, 4, …, 512 (repeated). The receptive field grows exponentially (1,024 steps per stack) and handles very long sequences (audio).

## Key Concepts
- **Recurrent layer**: ŷ(t) = ϕ(Wxᵀx(t) + Wŷᵀŷ(t−1) + b); input shape [batch, time steps, features]; `input_shape=[None, n_features]` handles any length.
- **Memory cell / hidden state h(t)**: may differ from the output.
- **`return_sequences=True`**: required on every recurrent layer except possibly the last; forgetting it feeds 2D to the next RNN (error).
- **`TimeDistributed`**: apply any vector layer at every time step (Dense already handles 3D).
- **MAE, MAPE, MSE**: MAPE puts errors in perspective across scales; MSE when large errors hurt quadratically.
- **Stationary series**: statistical properties constant over time.
- **Causal padding**: pad only on the left so outputs never peek ahead.
- **Splitting time series**: across time (train 2016–2018, valid Jan–May 2019, test Jun 2019+); across entities only if they're not correlated.

## Mental Models
- Think of an RNN unrolled through time as **a very deep feedforward net sharing weights across layers**, which explains its unstable gradients and the BPTT cost.
- Think of **LSTM as a conveyor belt (c) with valves**: learn what to write (input), keep (forget), and read (output).
- **Dory the fish**: simple RNNs forget the start of long sequences; gates or dilated convolutions fix it.
- **Seq-to-seq for training signal**: more outputs per window give more gradients, a bit like an auxiliary loss at every step.
- **Patterns must persist**: a forecaster trained on 2016–2019 fails in 2020 (Covid). Validate on recent data and monitor in production.

## Anti-patterns
- **Skipping the naive baseline**: you can't tell whether a fancy model is good.
- **Evaluating on one forecast day**.
- **Single-neuron SimpleRNN with tanh output on targets > 1**: MAE > 100,000. Use more units and a linear Dense output.
- **Shuffling within windows** (breaks order) or not shuffling windows (breaks IID).
- **ReLU in RNNs without care**: exploding outputs.
- **Batch norm between time steps**: use layer norm.
- **Long iterative multi-step forecasts**: error accumulation.

## Code Examples
```python
from statsmodels.tsa.arima.model import ARIMA
model = ARIMA(rail_series, order=(1, 0, 0), seasonal_order=(0, 1, 1, 7)).fit()
y_pred = model.forecast()

seq_length = 56
train_ds = tf.keras.utils.timeseries_dataset_from_array(
    rail_train.to_numpy(), targets=rail_train[seq_length:],
    sequence_length=seq_length, batch_size=32, shuffle=True, seed=42)

def to_windows(dataset, length):
    dataset = dataset.window(length, shift=1, drop_remainder=True)
    return dataset.flat_map(lambda window_ds: window_ds.batch(length))

def to_seq2seq_dataset(series, seq_length=56, ahead=14, target_col=1,
                       batch_size=32, shuffle=False, seed=None):
    ds = to_windows(tf.data.Dataset.from_tensor_slices(series), ahead + 1)
    ds = to_windows(ds, seq_length).map(lambda S: (S[:, 0], S[:, 1:, 1]))
    if shuffle:
        ds = ds.shuffle(8 * batch_size, seed=seed)
    return ds.batch(batch_size)

seq2seq_model = tf.keras.Sequential([
    tf.keras.layers.GRU(32, return_sequences=True, input_shape=[None, 5]),
    tf.keras.layers.Dense(14)])

wavenet_model = tf.keras.Sequential()
wavenet_model.add(tf.keras.layers.Input(shape=[None, 5]))
for rate in (1, 2, 4, 8) * 2:
    wavenet_model.add(tf.keras.layers.Conv1D(filters=32, kernel_size=2, padding="causal",
                                             activation="relu", dilation_rate=rate))
wavenet_model.add(tf.keras.layers.Conv1D(filters=14, kernel_size=1))
```

```python
class LNSimpleRNNCell(tf.keras.layers.Layer):
    def __init__(self, units, activation="tanh", **kwargs):
        super().__init__(**kwargs)
        self.state_size = units
        self.output_size = units
        self.simple_rnn_cell = tf.keras.layers.SimpleRNNCell(units, activation=None)
        self.layer_norm = tf.keras.layers.LayerNormalization()
        self.activation = tf.keras.activations.get(activation)

    def call(self, inputs, states):
        outputs, new_states = self.simple_rnn_cell(inputs, states)
        norm_outputs = self.activation(self.layer_norm(outputs))
        return norm_outputs, [norm_outputs]
# usage: tf.keras.layers.RNN(LNSimpleRNNCell(32), return_sequences=True, input_shape=[None, 5])
```

## Reference Tables
| Model (rail, validation Mar–May 2019) | MAE |
|---|---|
| Naive (t − 7) | 42,143 |
| SARIMA(1,0,0)(0,1,1,7), retrained daily | 32,041 |
| Linear (Dense on 56 days, Huber) | 37,866 |
| SimpleRNN(1) | > 100,000 |
| SimpleRNN(32) + Dense(1) | 27,703 |
| Deep RNN (3 × SimpleRNN(32)) | 31,211 (too big) |
| Multivariate RNN (bus, rail, next day type) | **22,062** |
| Seq2seq t+1 / t+2 / t+14 | 25,519 / 26,274 / 34,322 |

| Cell / layer | Memory | Notes |
|---|---|---|
| SimpleRNN | Short | Baseline; tanh |
| LSTM | Long (c + h) | Optimized GPU kernel (cuDNN) |
| GRU | Long (single h) | Simpler, similar accuracy |
| Conv1D (stride) | Extends RNN reach | Downsample before RNN |
| WaveNet (dilated causal Conv1D) | Very long | Fast, parallel; audio |

## Worked Example
**Diagnosing seasonality**: daily ridership shows strong weekly seasonality, so lag-7 naive forecasts track closely, except Memorial Day (holiday, `day_type` U). Monthly means + 12-month rolling average show yearly seasonality (clearer for rail) and a downward 2016–2019 trend. `diff(12)` removes both, giving a roughly stationary series. Adding *tomorrow's* day type (known in advance) as a one-hot input, plus the bus series, drops the RNN MAE from 27,703 to **22,062**. A known-future covariate matters more than architecture tweaks.

## Key Takeaways
1. Start every forecasting task with naive seasonal and SARIMA baselines, evaluated with rolling-origin forecasts.
2. Window series with `timeseries_dataset_from_array` or `window/flat_map`; split by time; shuffle windows.
3. Scale targets (e.g. /1e6); use Huber loss and early stopping; a linear Dense output (no tanh cap).
4. Add exogenous and known-future features (multivariate) before making the network deeper.
5. For multi-step forecasts prefer seq-to-seq (`return_sequences=True` + Dense(horizon)).
6. Use LSTM/GRU or Conv1D/WaveNet for long sequences; layer norm and recurrent dropout for stability; MC dropout for error bars.
7. Revalidate on recent data: regime shifts break learned patterns.

## Connects To
- **Ch 11**: unstable gradients, gradient clipping, MC dropout.
- **Ch 13**: `tf.data` windowing and pipelines.
- **Ch 14**: Conv layers, dilation, causal padding.
- **Ch 16**: RNNs for NLP, encoder–decoder, attention and transformers (which largely replace RNNs).
