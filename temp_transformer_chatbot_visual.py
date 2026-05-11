# temp_transformer_chatbot_visual.py
#
# Tiny decoder-only Transformer chatbot training visualization.
#
# This code follows the same style as temp_fan_sine.py.
#
# Instead of learning:
#   y = sin(freq * x)
#
# It learns:
#   next character prediction for chatbot-style text
#
# Output:
#   training_video_out_transformer/
#     ├── transformer_chatbot_training_trace.npz
#     ├── tiny_transformer_chatbot.pt
#     └── transformer_chatbot_training_dynamic.mp4
#
# Run:
#   python3 temp_transformer_chatbot_visual.py
#
# Open:
#   firefox training_video_out_transformer/transformer_chatbot_training_dynamic.mp4

import os
import math
import string
import textwrap
import numpy as np

import torch
import torch.nn as nn
import torch.nn.functional as F

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.animation import FFMpegWriter


# ============================================================
# 1. Config
# ============================================================

OUT_DIR = "training_video_out_transformer"
os.makedirs(OUT_DIR, exist_ok=True)

SEED = 0

NUM_EPOCHS = 2500
SAVE_EVERY = 25

LR = 3e-4

BATCH_SIZE = 32
BLOCK_SIZE = 128

N_EMBD = 128
N_HEAD = 4
N_LAYER = 4
DROPOUT = 0.1

VIDEO_FPS = 20

VIDEO_NAME = os.path.join(
    OUT_DIR,
    "transformer_chatbot_training_dynamic.mp4"
)

NPZ_NAME = os.path.join(
    OUT_DIR,
    "transformer_chatbot_training_trace.npz"
)

CKPT_NAME = os.path.join(
    OUT_DIR,
    "tiny_transformer_chatbot.pt"
)

DEVICE = "cuda" if torch.cuda.is_available() else "cpu"

FIXED_USER_PROMPT = "what is transformer"

MAX_NEW_TOKENS = 120
TEMPERATURE = 0.75
TOP_K = 20


# ============================================================
# 2. Reproducibility
# ============================================================

torch.manual_seed(SEED)
np.random.seed(SEED)

if DEVICE == "cuda":
    torch.cuda.manual_seed_all(SEED)


# ============================================================
# 3. Tiny chatbot dataset
# ============================================================

def build_training_text() -> str:
    """
    Small educational chatbot dataset.

    This model is intentionally tiny.
    It mostly learns/memorizes short chatbot-style patterns.

    That is okay because the goal is not to build ChatGPT.
    The goal is to visualize how a decoder-only Transformer learns.
    """

    pairs = [
        (
            "hello",
            "Hello. I am a tiny Transformer chatbot."
        ),
        (
            "hi",
            "Hi. Ask me something about Transformers."
        ),
        (
            "who are you",
            "I am a small decoder-only Transformer model."
        ),
        (
            "what is transformer",
            "A Transformer is a neural network based on attention."
        ),
        (
            "what is attention",
            "Attention lets each token look at previous tokens and decide what is important."
        ),
        (
            "what is self attention",
            "Self-attention compares tokens inside the same sequence."
        ),
        (
            "what is causal attention",
            "Causal attention prevents the model from seeing future tokens."
        ),
        (
            "why causal mask",
            "The causal mask makes text generation autoregressive."
        ),
        (
            "what is token",
            "A token is a unit of text processed by the model."
        ),
        (
            "what is embedding",
            "An embedding converts a token into a vector."
        ),
        (
            "what is positional embedding",
            "A positional embedding tells the model where a token is located."
        ),
        (
            "what is multi head attention",
            "Multi-head attention lets the model attend to information in several ways."
        ),
        (
            "what is feed forward network",
            "The feed-forward network transforms each token representation independently."
        ),
        (
            "what is residual connection",
            "A residual connection adds the input back to the output to stabilize training."
        ),
        (
            "what is layer norm",
            "Layer normalization stabilizes activations inside the Transformer."
        ),
        (
            "what is decoder only transformer",
            "A decoder-only Transformer predicts the next token from previous tokens."
        ),
        (
            "is gpt decoder only",
            "Yes. GPT-style models are decoder-only Transformers."
        ),
        (
            "how does chatbot generate answer",
            "It predicts one token at a time and appends it to the context."
        ),
        (
            "why transformer is powerful",
            "Because attention can model long-range relationships in a sequence."
        ),
        (
            "can transformer be used for rtl",
            "Yes. A Transformer can learn patterns from logs, code, and sequential debug traces."
        ),
        (
            "can transformer help fpga debug",
            "It can help analyze sequential board logs and suggest debugging actions."
        ),
        (
            "what is training",
            "Training adjusts model weights to reduce prediction error."
        ),
        (
            "what is loss",
            "Loss measures how wrong the model prediction is."
        ),
        (
            "what is cross entropy",
            "Cross entropy is commonly used for next-token prediction."
        ),
        (
            "what is inference",
            "Inference means using the trained model to generate outputs."
        ),
        (
            "what is overfitting",
            "Overfitting happens when the model memorizes training examples too strongly."
        ),
        (
            "what is temperature",
            "Temperature controls randomness during generation."
        ),
        (
            "what is top k sampling",
            "Top-k sampling restricts generation to the k most likely next tokens."
        ),
        (
            "explain transformer simply",
            "A Transformer reads previous tokens, attends to useful ones, and predicts the next token."
        ),
        (
            "explain attention simply",
            "Attention is like asking: which previous words matter most right now?"
        ),
        (
            "what should i learn first",
            "First learn token embeddings, positional embeddings, causal attention, and next-token prediction."
        ),
        (
            "how are you",
            "I am running as a tiny Transformer example."
        ),
        (
            "thank you",
            "You are welcome."
        ),
        (
            "bye",
            "Goodbye. Keep learning Transformers step by step."
        ),
    ]

    conversations = []

    for user_text, bot_text in pairs:
        conversations.append(
            f"User: {user_text}\n"
            f"Bot: {bot_text}\n"
        )

    text = "\n".join(conversations)

    # Repeat many times so the tiny model can learn quickly.
    text = text * 200

    return text


# ============================================================
# 4. Character tokenizer
# ============================================================

class CharTokenizer:
    """
    Very simple character-level tokenizer.

    Real LLMs usually use BPE/SentencePiece tokenizers.
    This educational model uses characters because it is easier to inspect.
    """

    def __init__(self):
        chars = list(string.printable)

        if "\n" not in chars:
            chars.append("\n")

        self.itos = chars
        self.stoi = {ch: i for i, ch in enumerate(chars)}
        self.vocab_size = len(chars)

    def encode(self, text: str):
        return [
            self.stoi.get(ch, self.stoi["?"])
            for ch in text
        ]

    def decode(self, ids):
        return "".join(
            self.itos[int(i)]
            for i in ids
        )


# ============================================================
# 5. Transformer components
# ============================================================

class CausalSelfAttention(nn.Module):
    """
    Multi-head causal self-attention.

    x:
        [B, T, C]

    output:
        [B, T, C]

    attention map:
        [B, n_head, T, T]
    """

    def __init__(self):
        super().__init__()

        assert N_EMBD % N_HEAD == 0

        self.n_head = N_HEAD
        self.head_dim = N_EMBD // N_HEAD

        self.qkv_proj = nn.Linear(N_EMBD, 3 * N_EMBD)
        self.out_proj = nn.Linear(N_EMBD, N_EMBD)

        self.attn_dropout = nn.Dropout(DROPOUT)
        self.resid_dropout = nn.Dropout(DROPOUT)

        mask = torch.tril(
            torch.ones(BLOCK_SIZE, BLOCK_SIZE)
        )

        self.register_buffer(
            "causal_mask",
            mask.view(1, 1, BLOCK_SIZE, BLOCK_SIZE)
        )

    def forward(self, x, return_attention=False):
        B, T, C = x.shape

        qkv = self.qkv_proj(x)

        q, k, v = qkv.split(C, dim=2)

        q = q.view(B, T, self.n_head, self.head_dim)
        k = k.view(B, T, self.n_head, self.head_dim)
        v = v.view(B, T, self.n_head, self.head_dim)

        q = q.transpose(1, 2)
        k = k.transpose(1, 2)
        v = v.transpose(1, 2)

        # ----------------------------------------------------
        # Core attention equation
        # ----------------------------------------------------
        # att score = Q K^T / sqrt(d_head)
        # shape:
        #   [B, n_head, T, T]
        # ----------------------------------------------------
        att = (q @ k.transpose(-2, -1)) / math.sqrt(self.head_dim)

        # ----------------------------------------------------
        # Causal mask
        # ----------------------------------------------------
        # Current token cannot see future tokens.
        # ----------------------------------------------------
        att = att.masked_fill(
            self.causal_mask[:, :, :T, :T] == 0,
            float("-inf")
        )

        # ----------------------------------------------------
        # Attention probability
        # ----------------------------------------------------
        att = F.softmax(att, dim=-1)

        att_for_visual = att.detach()

        att = self.attn_dropout(att)

        # ----------------------------------------------------
        # Weighted sum of values
        # ----------------------------------------------------
        y = att @ v

        y = y.transpose(1, 2).contiguous().view(B, T, C)

        y = self.out_proj(y)
        y = self.resid_dropout(y)

        if return_attention:
            return y, att_for_visual

        return y, None


class FeedForward(nn.Module):
    """
    Position-wise MLP inside Transformer block.
    """

    def __init__(self):
        super().__init__()

        self.net = nn.Sequential(
            nn.Linear(N_EMBD, 4 * N_EMBD),
            nn.GELU(),
            nn.Linear(4 * N_EMBD, N_EMBD),
            nn.Dropout(DROPOUT),
        )

    def forward(self, x):
        return self.net(x)


class TransformerBlock(nn.Module):
    """
    Pre-LN Transformer block.

        x = x + Attention(LayerNorm(x))
        x = x + FFN(LayerNorm(x))
    """

    def __init__(self):
        super().__init__()

        self.ln1 = nn.LayerNorm(N_EMBD)
        self.attn = CausalSelfAttention()

        self.ln2 = nn.LayerNorm(N_EMBD)
        self.ff = FeedForward()

    def forward(self, x, return_attention=False):
        attn_out, attn_map = self.attn(
            self.ln1(x),
            return_attention=return_attention
        )

        x = x + attn_out
        x = x + self.ff(self.ln2(x))

        return x, attn_map


class TinyTransformerChatbot(nn.Module):
    """
    GPT-style decoder-only Transformer.
    """

    def __init__(self, vocab_size: int):
        super().__init__()

        self.vocab_size = vocab_size

        self.token_emb = nn.Embedding(vocab_size, N_EMBD)
        self.pos_emb = nn.Embedding(BLOCK_SIZE, N_EMBD)

        self.blocks = nn.ModuleList([
            TransformerBlock()
            for _ in range(N_LAYER)
        ])

        self.ln_f = nn.LayerNorm(N_EMBD)
        self.lm_head = nn.Linear(N_EMBD, vocab_size)

        self.apply(self._init_weights)

    def _init_weights(self, module):
        if isinstance(module, nn.Linear):
            nn.init.normal_(
                module.weight,
                mean=0.0,
                std=0.02
            )

            if module.bias is not None:
                nn.init.zeros_(module.bias)

        elif isinstance(module, nn.Embedding):
            nn.init.normal_(
                module.weight,
                mean=0.0,
                std=0.02
            )

    def forward(self, idx, targets=None, return_attention=False):
        B, T = idx.shape

        if T > BLOCK_SIZE:
            raise ValueError(
                f"Sequence length {T} exceeds BLOCK_SIZE={BLOCK_SIZE}"
            )

        positions = torch.arange(
            0,
            T,
            device=idx.device
        )

        tok = self.token_emb(idx)
        pos = self.pos_emb(positions)

        x = tok + pos

        attention_maps = []

        for block in self.blocks:
            x, attn_map = block(
                x,
                return_attention=return_attention
            )

            if return_attention:
                attention_maps.append(attn_map)

        x = self.ln_f(x)

        logits = self.lm_head(x)

        loss = None

        if targets is not None:
            B, T, V = logits.shape

            loss = F.cross_entropy(
                logits.view(B * T, V),
                targets.view(B * T)
            )

        if return_attention:
            return logits, loss, attention_maps

        return logits, loss

    @torch.no_grad()
    def generate(
        self,
        idx,
        max_new_tokens=120,
        temperature=0.75,
        top_k=20,
    ):
        """
        Autoregressive generation.
        """

        self.eval()

        for _ in range(max_new_tokens):
            idx_cond = idx[:, -BLOCK_SIZE:]

            logits, _ = self(idx_cond)

            logits = logits[:, -1, :]
            logits = logits / temperature

            if top_k is not None:
                values, _ = torch.topk(
                    logits,
                    min(top_k, logits.size(-1))
                )

                cutoff = values[:, [-1]]

                logits = torch.where(
                    logits < cutoff,
                    torch.full_like(logits, float("-inf")),
                    logits
                )

            probs = F.softmax(logits, dim=-1)

            next_id = torch.multinomial(
                probs,
                num_samples=1
            )

            idx = torch.cat(
                [idx, next_id],
                dim=1
            )

        return idx


# ============================================================
# 6. Dataset batching
# ============================================================

def get_batch(data_ids: torch.Tensor):
    """
    Create random next-token prediction batch.

    x:
        [BATCH_SIZE, BLOCK_SIZE]

    y:
        same sequence shifted by one character
    """

    max_start = len(data_ids) - BLOCK_SIZE - 1

    starts = torch.randint(
        low=0,
        high=max_start,
        size=(BATCH_SIZE,)
    )

    x = torch.stack([
        data_ids[i:i + BLOCK_SIZE]
        for i in starts
    ])

    y = torch.stack([
        data_ids[i + 1:i + BLOCK_SIZE + 1]
        for i in starts
    ])

    return x.to(DEVICE), y.to(DEVICE)


@torch.no_grad()
def estimate_loss(model, train_ids, val_ids):
    model.eval()

    x_train, y_train = get_batch(train_ids)
    _, train_loss = model(x_train, y_train)

    x_val, y_val = get_batch(val_ids)
    _, val_loss = model(x_val, y_val)

    return float(train_loss.item()), float(val_loss.item())


# ============================================================
# 7. Text generation + attention extraction
# ============================================================

def clean_text_for_plot(text: str) -> str:
    """
    Remove strange control characters for matplotlib text display.
    """

    cleaned = []

    for ch in text:
        if ch in "\n\t":
            cleaned.append(ch)
        elif ch in string.printable and ch not in "\x0b\x0c\r":
            cleaned.append(ch)
        else:
            cleaned.append(" ")

    return "".join(cleaned)


@torch.no_grad()
def generate_answer(model, tokenizer, user_prompt: str):
    model.eval()

    prompt = f"User: {user_prompt}\nBot:"

    ids = tokenizer.encode(prompt)

    idx = torch.tensor(
        [ids],
        dtype=torch.long,
        device=DEVICE
    )

    out = model.generate(
        idx,
        max_new_tokens=MAX_NEW_TOKENS,
        temperature=TEMPERATURE,
        top_k=TOP_K
    )

    full_text = tokenizer.decode(
        out[0].detach().cpu().tolist()
    )

    answer = full_text[len(prompt):]

    if "\nUser:" in answer:
        answer = answer.split("\nUser:")[0]

    answer = answer.strip()

    if len(answer) == 0:
        answer = "(empty / still random)"

    answer = clean_text_for_plot(answer)

    return answer


@torch.no_grad()
def get_prompt_attention(model, tokenizer, user_prompt: str):
    """
    Extract attention map from final Transformer block, head 0.

    We visualize attention over the fixed prompt:
        User: what is transformer
        Bot:

    attention_map shape:
        [T, T]
    """

    model.eval()

    prompt = f"User: {user_prompt}\nBot:"

    ids = tokenizer.encode(prompt)

    idx = torch.tensor(
        [ids],
        dtype=torch.long,
        device=DEVICE
    )

    _, _, attention_maps = model(
        idx,
        targets=None,
        return_attention=True
    )

    # Last layer, first batch, first head.
    attn = attention_maps[-1][0, 0]

    attn = attn.detach().cpu().numpy().astype(np.float32)

    return attn


# ============================================================
# 8. Initialize dataset, tokenizer, model
# ============================================================

tokenizer = CharTokenizer()

text = build_training_text()
ids = torch.tensor(
    tokenizer.encode(text),
    dtype=torch.long
)

split_idx = int(0.9 * len(ids))

train_ids = ids[:split_idx]
val_ids = ids[split_idx:]

model = TinyTransformerChatbot(
    vocab_size=tokenizer.vocab_size
).to(DEVICE)

optimizer = torch.optim.AdamW(
    model.parameters(),
    lr=LR,
    weight_decay=0.01
)

print(f"Using device: {DEVICE}")
print("Target task: character-level next-token prediction")
print(f"Fixed visualization prompt: {FIXED_USER_PROMPT}")
print("Start training...\n")


# ============================================================
# 9. Training + history saving
# ============================================================

train_losses = []
val_losses = []

saved_epochs = []
generated_history = []
attention_history = []

for epoch in range(NUM_EPOCHS + 1):

    # --------------------------------------------------------
    # Save/evaluate initial random model at epoch 0.
    # Then train from epoch 1.
    # --------------------------------------------------------
    if epoch > 0:
        model.train()

        x, y = get_batch(train_ids)

        logits, loss = model(x, y)

        optimizer.zero_grad(set_to_none=True)
        loss.backward()
        optimizer.step()

    # --------------------------------------------------------
    # Evaluate
    # --------------------------------------------------------
    train_loss_eval, val_loss_eval = estimate_loss(
        model,
        train_ids,
        val_ids
    )

    train_losses.append(train_loss_eval)
    val_losses.append(val_loss_eval)

    # --------------------------------------------------------
    # Save generated answer and attention map for video
    # --------------------------------------------------------
    if epoch % SAVE_EVERY == 0:
        answer = generate_answer(
            model,
            tokenizer,
            FIXED_USER_PROMPT
        )

        attn = get_prompt_attention(
            model,
            tokenizer,
            FIXED_USER_PROMPT
        )

        saved_epochs.append(epoch)
        generated_history.append(answer)
        attention_history.append(attn)

    # --------------------------------------------------------
    # Print progress
    # --------------------------------------------------------
    if epoch % 100 == 0:
        print(
            f"Epoch {epoch:5d}/{NUM_EPOCHS} | "
            f"Train Loss: {train_losses[-1]:.6f} | "
            f"Val Loss: {val_losses[-1]:.6f}"
        )


saved_epochs = np.array(
    saved_epochs,
    dtype=np.int32
)

train_losses = np.array(
    train_losses,
    dtype=np.float32
)

val_losses = np.array(
    val_losses,
    dtype=np.float32
)

attention_history = np.stack(
    attention_history,
    axis=0
).astype(np.float32)

generated_history_np = np.array(
    generated_history,
    dtype=object
)

np.savez(
    NPZ_NAME,
    saved_epochs=saved_epochs,
    generated_history=generated_history_np,
    attention_history=attention_history,
    train_losses=train_losses,
    val_losses=val_losses,
    num_epochs=NUM_EPOCHS,
    save_every=SAVE_EVERY,
    block_size=BLOCK_SIZE,
    n_embd=N_EMBD,
    n_head=N_HEAD,
    n_layer=N_LAYER,
    fixed_user_prompt=FIXED_USER_PROMPT,
)

torch.save(
    {
        "model_state_dict": model.state_dict(),
        "vocab": tokenizer.itos,
        "config": {
            "block_size": BLOCK_SIZE,
            "n_embd": N_EMBD,
            "n_head": N_HEAD,
            "n_layer": N_LAYER,
            "dropout": DROPOUT,
        }
    },
    CKPT_NAME
)

print(f"\nSaved trace to: {NPZ_NAME}")
print(f"Saved checkpoint to: {CKPT_NAME}")


# ============================================================
# 10. Render video
# ============================================================

print("Start rendering video...")

# Vertical reels-style format:
# 6 inch * 180 dpi = 1080 px
# 10.67 inch * 180 dpi = 1920 px
fig = plt.figure(figsize=(6, 10.67))

ax_text = fig.add_axes([0.08, 0.66, 0.84, 0.25])
ax_attn = fig.add_axes([0.12, 0.36, 0.76, 0.22])
ax_loss = fig.add_axes([0.12, 0.12, 0.82, 0.16])

metadata = dict(
    title="Tiny Transformer Chatbot Training Visualization"
)

writer = FFMpegWriter(
    fps=VIDEO_FPS,
    metadata=metadata
)

prompt_for_title = f"User: {FIXED_USER_PROMPT}\\nBot:"

with writer.saving(fig, VIDEO_NAME, dpi=180):

    for i, epoch in enumerate(saved_epochs):

        ax_text.clear()
        ax_attn.clear()
        ax_loss.clear()

        answer = generated_history[i]
        attn = attention_history[i]

        # ----------------------------------------------------
        # Text generation panel
        # ----------------------------------------------------
        ax_text.axis("off")

        wrapped_answer = textwrap.fill(
            answer,
            width=48
        )

        text_panel = (
            "Tiny Decoder-only Transformer Chatbot\n\n"
            f"Fixed prompt:\n{prompt_for_title}\n\n"
            f"Generated answer at epoch {epoch}:\n"
            f"{wrapped_answer}"
        )

        ax_text.text(
            0.0,
            1.0,
            text_panel,
            transform=ax_text.transAxes,
            va="top",
            ha="left",
            fontsize=12,
            family="monospace",
            bbox=dict(
                boxstyle="round,pad=0.6",
                facecolor="white",
                alpha=0.92,
            ),
        )

        ax_text.set_title(
            "Transformer Chatbot Learning Process",
            fontsize=18,
            fontweight="bold",
            pad=18,
        )

        # ----------------------------------------------------
        # Attention heatmap
        # ----------------------------------------------------
        im = ax_attn.imshow(
            attn,
            aspect="auto",
            origin="lower"
        )

        ax_attn.set_title(
            "Causal Self-Attention Heatmap\n"
            "Last Transformer Block, Head 0",
            fontsize=12,
            fontweight="bold"
        )

        ax_attn.set_xlabel("key token position")
        ax_attn.set_ylabel("query token position")

        ax_attn.text(
            0.02,
            0.95,
            "Lower-triangular structure = no future-token access",
            transform=ax_attn.transAxes,
            va="top",
            ha="left",
            fontsize=8,
            bbox=dict(
                boxstyle="round,pad=0.35",
                facecolor="white",
                alpha=0.82,
            ),
        )

        # ----------------------------------------------------
        # Loss curve
        # ----------------------------------------------------
        epoch_axis = np.arange(len(train_losses))

        ax_loss.plot(
            epoch_axis[:epoch + 1],
            train_losses[:epoch + 1],
            label="Train Loss",
            linewidth=1.8,
        )

        ax_loss.plot(
            epoch_axis[:epoch + 1],
            val_losses[:epoch + 1],
            label="Validation Loss",
            linewidth=1.8,
        )

        ax_loss.scatter(
            [epoch],
            [val_losses[epoch]],
            s=25,
        )

        ax_loss.set_xlim(0, NUM_EPOCHS)

        max_loss_for_plot = max(
            float(np.max(train_losses[:min(200, len(train_losses))])),
            float(np.max(val_losses[:min(200, len(val_losses))])),
        )

        ax_loss.set_ylim(
            0,
            max_loss_for_plot * 1.05
        )

        ax_loss.set_xlabel("epoch")
        ax_loss.set_ylabel("cross entropy loss")

        ax_loss.grid(True, alpha=0.3)
        ax_loss.legend(loc="upper right", fontsize=8)

        ax_loss.text(
            0.98,
            0.82,
            f"val loss = {val_losses[epoch]:.6f}",
            transform=ax_loss.transAxes,
            va="top",
            ha="right",
            fontsize=9,
            bbox=dict(
                boxstyle="round,pad=0.35",
                facecolor="white",
                alpha=0.82,
            ),
        )

        writer.grab_frame()

    # Hold final frame for 2 seconds.
    final_hold_frames = VIDEO_FPS * 2

    for _ in range(final_hold_frames):
        writer.grab_frame()


plt.close(fig)

print(f"Saved video to: {VIDEO_NAME}")
print("\nDone.")

print("\nOpen with browser:")
print(f"firefox {VIDEO_NAME}")
