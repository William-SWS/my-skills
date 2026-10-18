# Chapter 16: Natural Language Processing with RNNs and Attention

## Core Idea
NLP progresses from a **char-RNN language model** (generate Shakespeare; stateless vs stateful) to **word-level sentiment analysis** (masking, ragged tensors, pretrained encoders), to an **encoder–decoder for neural machine translation** (bidirectional encoder, beam search), to **attention** (Bahdanau, Luong) and the **Transformer** ("Attention Is All You Need": positional encodings, multi-head attention, masking). It ends with the avalanche of pretrained transformers (GPT, BERT, T5, ViT…) and **Hugging Face's Transformers**.

## Frameworks Introduced
- **Char-RNN language model**: `TextVectorization(split="character", standardize="lower")` → windows of length 100 (target = input shifted by 1) → Embedding(16) → GRU(128, return_sequences) → Dense(39, softmax). Window length bounds the patterns it can learn.
- **Sampling with temperature**: divide logits by T. T → 0 means greedy/repetitive; T = 1 is natural; T ≫ 1 is random gibberish. Better: **top-k** or **nucleus (top-p) sampling**. Greedy decoding tends to repeat itself.
- **Stateless vs stateful RNN**: stateful keeps the final hidden state as the initial state for the next batch, so it can learn longer patterns. It needs **non-overlapping consecutive windows** (`shift=length`), batch-aligned sequences, `stateful=True`, a fixed `batch_input_shape`, and `reset_states()` each epoch. Copy its weights into a stateless twin for inference at other batch sizes.
- **Tokenization choices**: words by spaces (English OK), **subword**: **BPE** (Sennrich 2015), **WordPiece**, **SentencePiece/unigram with subword regularization** (Kudo 2018; language-independent, handles spaces). Tools: TF Text, Hugging Face Tokenizers.
- **Masking padding**: `Embedding(mask_zero=True)` propagates the mask to RNNs, Dense, Bidirectional, TimeDistributed, Add (Conv1D doesn't support it). Or pass `mask=` explicitly (functional API), or use **ragged tensors** (`TextVectorization(ragged=True)`). cuDNN LSTM/GRU support masks only with post-padding and default hyperparameters.
- **Reuse pretrained language components**: Universal Sentence Encoder from TF Hub (`trainable=True` to fine-tune) gets > 90% on IMDb vs ~80% for a GRU trained from scratch. Pretrained word embeddings (Word2vec, GloVe, FastText) are context-free; contextual models (ELMo, ULMFiT, transformers) are better.
- **Encoder–decoder NMT**: encoder LSTM (`return_state=True`) gives its state as the decoder LSTM's initial state. The decoder input is the target shifted right with `startofseq` (**teacher forcing**); the target ends with `endofseq`. At inference, feed back the previously predicted word, one step at a time.
- **Bidirectional encoder**: `Bidirectional(LSTM(256, return_state=True))` returns 4 states; concatenate short-term (0, 2) and long-term (1, 3) for the decoder. **The decoder must remain causal.**
- **Beam search**: keep the top-k (beam width) partial translations by cumulative probability at each step. This recovers from early mistakes ("me gustan…" → "me gusta el fútbol").
- **Attention mechanisms**: at each decoder step, a weighted sum of all encoder outputs, with weights α = softmax(alignment scores). **Bahdanau (concatenative/additive)**: v·tanh(W[h; y]) (`AdditiveAttention`); **Luong (multiplicative)**: dot or general hᵀWy (`Attention`). Think of attention as a **differentiable dictionary lookup**: queries match keys, which returns values.
- **Transformer (Vaswani 2017)**: encoder stack (N = 6) of [multi-head self-attention → Add & LayerNorm → FFN (Dense ReLU → Dense) → Add & LayerNorm]; decoder stack with **masked (causal) self-attention**, **cross-attention** (Q from decoder, K/V from encoder), FFN. **Positional encodings** (sine/cosine or learned) are added to the embeddings. No recurrence or convolution, so it's fully parallel.
- **Scaled dot-product attention**: softmax(QKᵀ/√d_keys)V; mask with a large negative value before the softmax. **Multi-head**: h parallel attention heads over different linear projections (subspaces: verb-ness, tense, position…), then concatenate and project.
- **Masking in transformers**: padding mask `not_equal(ids, 0)[:, tf.newaxis]` for keys; **causal mask** `tf.linalg.band_part(ones((L, L), bool), -1, 0)` (lower triangular); combine with `&` in the decoder self-attention.
- **Pretraining paradigms**: GPT (decoder-only, causal LM, then fine-tune; GPT-2/3 zero/few-shot), **BERT** (encoder-only; **MLM** masks 15% of tokens: 80% `[MASK]`, 10% random, 10% unchanged; NSP; `<CLS>` token for classification), T5 (text-to-text encoder–decoder), plus RoBERTa, DistilBERT (distillation), PaLM, Chinchilla. **Chain-of-thought prompting** improves reasoning.
- **Vision transformers**: ViT (image → 16×16 patches as tokens); DeiT (data-efficient, distillation from a CNN); Perceiver (cross-attention to a latent bottleneck); DINO (self-supervised), model soups (weight averaging). Transformers have weaker **inductive biases** than CNNs, so they need more data.

## Key Concepts
- **Language model**: predicts the next token; it implicitly learns higher-level features (OpenAI's "sentiment neuron").
- **SOS/EOS tokens**; **teacher forcing**; **autoregressive decoding**.
- **BLEU**: n-gram precision vs human references (NMT metric).
- **Sampled softmax** (`tf.nn.sampled_softmax_loss`) for huge vocabularies during training.
- **Explainability**: attention maps show what the model focused on (e.g. a "wolf" classifier keying on snow). This can be a legal requirement (loans).
- **Bias and fairness**: a DistilBERT sentiment pipeline rates "I am from India" positive and "I am from Iraq" negative. Bias comes from the training data; evaluate subgroups.
- **Hugging Face**: `pipeline("sentiment-analysis")`; `AutoTokenizer` + `TFAutoModelForSequenceClassification`; outputs **logits**, so use `SparseCategoricalCrossentropy(from_logits=True)`; pass `tokenizer(...).data` to `fit()`.

## Mental Models
- Think of the **encoder–decoder bottleneck**: one state vector must carry a whole sentence. Attention removes the bottleneck by letting the decoder look back at every encoder output.
- Think of **self-attention as each word rewriting itself** by consulting every other word ("like" becomes "verb, present, positive, about soccer").
- **Inductive bias vs data**: CNN/RNN priors help on small data; transformers win with scale, or with distillation/augmentation (DeiT).
- **Pretrain then fine-tune** is the default NLP workflow: reach for TF Hub / Hugging Face before training from scratch.

## Anti-patterns
- **Greedy decoding / T = 1 sampling for quality text**: use beam search (translation) or top-k/top-p (generation).
- **Letting the model see padding**: use masks or ragged tensors.
- **Bidirectional decoders**: they cheat in training and fail at inference.
- **Overlapping windows for stateful RNNs**.
- **Treating `pipeline()` outputs as unbiased**.
- **Using the `"sparse_categorical_crossentropy"` string with HF logits outputs**.

## Code Examples
```python
def next_char(text, temperature=1):
    y_proba = shakespeare_model.predict([text])[0, -1:]
    rescaled_logits = tf.math.log(y_proba) / temperature
    char_id = tf.random.categorical(rescaled_logits, num_samples=1)[0, 0]
    return text_vec_layer.get_vocabulary()[char_id + 2]

model = tf.keras.Sequential([                      # sentiment, IMDb
    text_vec_layer,                                # TextVectorization(max_tokens=1000)
    tf.keras.layers.Embedding(vocab_size, 128, mask_zero=True),
    tf.keras.layers.GRU(128),
    tf.keras.layers.Dense(1, activation="sigmoid")])
```

```python
encoder_embeddings = encoder_embedding_layer(text_vec_layer_en(encoder_inputs))
decoder_embeddings = decoder_embedding_layer(text_vec_layer_es(decoder_inputs))
encoder = tf.keras.layers.Bidirectional(
    tf.keras.layers.LSTM(256, return_sequences=True, return_state=True))
encoder_outputs, *encoder_state = encoder(encoder_embeddings)
encoder_state = [tf.concat(encoder_state[::2], axis=-1),    # short-term
                 tf.concat(encoder_state[1::2], axis=-1)]   # long-term
decoder = tf.keras.layers.LSTM(512, return_sequences=True)
decoder_outputs = decoder(decoder_embeddings, initial_state=encoder_state)
attention_outputs = tf.keras.layers.Attention()([decoder_outputs, encoder_outputs])
Y_proba = tf.keras.layers.Dense(vocab_size, activation="softmax")(attention_outputs)
model = tf.keras.Model(inputs=[encoder_inputs, decoder_inputs], outputs=[Y_proba])
```

```python
Z = encoder_in                                     # transformer encoder block × N
for _ in range(N):
    skip = Z
    attn_layer = tf.keras.layers.MultiHeadAttention(num_heads=8, key_dim=embed_size,
                                                    dropout=0.1)
    Z = attn_layer(Z, value=Z, attention_mask=encoder_pad_mask)
    Z = tf.keras.layers.LayerNormalization()(tf.keras.layers.Add()([Z, skip]))
    skip = Z
    Z = tf.keras.layers.Dense(n_units, activation="relu")(Z)
    Z = tf.keras.layers.Dense(embed_size)(Z)
    Z = tf.keras.layers.Dropout(0.1)(Z)
    Z = tf.keras.layers.LayerNormalization()(tf.keras.layers.Add()([Z, skip]))
causal_mask = tf.linalg.band_part(tf.ones((batch_max_len_dec, batch_max_len_dec), tf.bool), -1, 0)
# decoder self-attn: attention_mask=causal_mask & decoder_pad_mask
# decoder cross-attn: attn_layer(Z, value=encoder_outputs, attention_mask=encoder_pad_mask)
```

## Reference Tables
| Attention | Score e(t,i) | Keras layer |
|---|---|---|
| Dot (Luong) | hᵀy | `Attention()` |
| General (Luong) | hᵀWy | – |
| Concat (Bahdanau) | vᵀtanh(W[h; y]) | `AdditiveAttention()` |
| Scaled dot-product (Transformer) | QKᵀ/√d | `MultiHeadAttention` |

| Model | Type | Pretraining | Use |
|---|---|---|---|
| GPT family | Decoder-only | Causal LM | Generation, few-shot |
| BERT / RoBERTa / DistilBERT | Encoder-only | MLM (+ NSP) | Classification, QA, NER |
| T5 | Encoder–decoder | Span corruption, text-to-text | Any text task |
| ViT / DeiT | Encoder | Supervised / distillation | Vision |

| IMDb sentiment approach | Val accuracy |
|---|---|
| GRU, no masking (padding hurts) | ~50% initially |
| GRU + `mask_zero=True` | > 80% |
| Universal Sentence Encoder (fine-tuned) + Dense | > 90% |

## Worked Example
**Why attention matters for NMT**: the plain encoder–decoder translates "I like soccer" → "me gusta el fútbol" (good), but "I like soccer and also going to the beach" → "me gusta el fútbol y a veces mismo al bus" ("…sometimes even the bus"): long-sentence memory fails. With a bidirectional encoder (`return_sequences=True`) + Luong `Attention([decoder_outputs, encoder_outputs])`, it gives "me gusta el fútbol y también ir a la playa", which is correct. **Beam search** (width 3) also fixes early-commitment errors: after step 1, "me" (75%); step 2 keeps "me gustan" (36%), "me gusta" (32%), "me encanta" (16%); by step 4 "me gusta el fútbol" (6%) wins.

## Key Takeaways
1. Character/word language models are the base of generation; control diversity with temperature, top-k, top-p.
2. Always mask padding (or use ragged tensors); prefer subword tokenization for real systems.
3. Reach for pretrained encoders (TF Hub, Hugging Face) before training text models from scratch.
4. Encoder–decoder + teacher forcing for seq2seq; a bidirectional encoder, a causal decoder; beam search at inference.
5. Attention (Q/K/V lookup) removes the RNN memory bottleneck; transformers use only attention + positional encodings + FFN + residual + layer norm.
6. Get the masks right: padding masks for keys, causal masks for decoder self-attention.
7. Audit pretrained models for bias; use attention maps for explainability.

## Connects To
- **Ch 13**: TextVectorization, embeddings, TF Hub.
- **Ch 15**: RNN/LSTM/GRU cells, seq2seq, windows.
- **Ch 14**: CNN encoders for image captioning; ViT vs CNN inductive bias.
- **Ch 17**: generative models (autoregressive LMs are generative).
- **Ch 19**: serving large models, distribution.
