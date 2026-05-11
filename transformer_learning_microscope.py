#!/usr/bin/env python3
# transformer_learning_microscope.py
#
# Visual microscope for understanding why a tiny Transformer chatbot trains well.
#
# It visualizes:
#   1. Generated answer over training
#   2. Top-k next-token probabilities after fixed prompt
#   3. Correct next-character probability over the target answer
#   4. Causal self-attention heatmap
#   5. Train / validation loss
#
# Output:
#   transformer_learning_microscope_out/
#     ├── transformer_learning_trace.npz
#     ├── tiny_transformer_microscope.pt
#     └── transformer_learning_microscope.mp4
#
# Run:
#   python3 transformer_learning_microscope.py
#
# Open:
#   firefox transformer_learning_microscope_out/transformer_learning_microscope.mp4

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

OUT_DIR = "transformer_learning_microscope_out"
os.makedirs(OUT_DIR, exist_ok=True)

VIDEO_NAME = os.path.join(OUT_DIR, "transformer_learning_microscope.mp4")
NPZ_NAME = os.path.join(OUT_DIR, "transformer_learning_trace.npz")
CKPT_NAME = os.path.join(OUT_DIR, "tiny_transformer_microscope.pt")

SEED = 0

NUM_EPOCHS = 2500
SAVE_EVERY = 25

BATCH_SIZE = 32
BLOCK_SIZE = 128

N_EMBD = 128
N_HEAD = 4
N_LAYER = 4
DROPOUT = 0.1

LR = 3e-4

TOP_K = 10
MAX_NEW_TOKENS = 90
VIDEO_FPS = 12

DEVICE = "cuda" if torch.cuda.is_available() else "cpu"

FIXED_USER_PROMPT = "what is transformer"

# Important:
# Training dataset uses:
#   Bot: A Transformer ...
# So after "Bot:" the correct next character is a space.
PROBE_PROMPT = f"User: {FIXED_USER_PROMPT}\nBot:"
PROBE_TARGET_ANSWER = " A Transformer is a neural network based on attention.\n"


# ============================================================
# 2. Reproducibility
# ============================================================

torch.manual_seed(SEED)
np.random.seed(SEED)

if DEVICE == "cuda":
    torch.cuda.manual_seed_all(SEED)


# ============================================================
# 3. Dataset
# ============================================================

def build_training_text() -> str:
    pairs = [
        ("hello", "Hello. I am a tiny Transformer chatbot."),
        ("hi", "Hi. Ask me something about Transformers."),
        ("who are you", "I am a small decoder-only Transformer model."),
        ("what is transformer", "A Transformer is a neural network based on attention."),
        ("what is attention", "Attention lets each token look at previous tokens and decide what is important."),
        ("what is self attention", "Self-attention compares tokens inside the same sequence."),
        ("what is causal attention", "Causal attention prevents the model from seeing future tokens."),
        ("why causal mask", "The causal mask makes text generation autoregressive."),
        ("what is token", "A token is a unit of text processed by the model."),
        ("what is embedding", "An embedding converts a token into a vector."),
        ("what is positional embedding", "A positional embedding tells the model where a token is located."),
        ("what is multi head attention", "Multi-head attention lets the model attend to information in several ways."),
        ("what is feed forward network", "The feed-forward network transforms each token representation independently."),
        ("what is residual connection", "A residual connection adds the input back to the output to stabilize training."),
        ("what is layer norm", "Layer normalization stabilizes activations inside the Transformer."),
        ("what is decoder only transformer", "A decoder-only Transformer predicts the next token from previous tokens."),
        ("is gpt decoder only", "Yes. GPT-style models are decoder-only Transformers."),
        ("how does chatbot generate answer", "It predicts one token at a time and appends it to the context."),
        ("why transformer is powerful", "Because attention can model long-range relationships in a sequence."),
        ("can transformer be used for rtl", "Yes. A Transformer can learn patterns from logs, code, and sequential debug traces."),
        ("can transformer help fpga debug", "It can help analyze sequential board logs and suggest debugging actions."),
        ("what is training", "Training adjusts model weights to reduce prediction error."),
        ("what is loss", "Loss measures how wrong the model prediction is."),
        ("what is cross entropy", "Cross entropy is commonly used for next-token prediction."),
        ("what is inference", "Inference means using the trained model to generate outputs."),
        ("what is overfitting", "Overfitting happens when the model memorizes training examples too strongly."),
        ("what is temperature", "Temperature controls randomness during generation."),
        ("what is top k sampling", "Top-k sampling restricts generation to the k most likely next tokens."),
        ("explain transformer simply", "A Transformer reads previous tokens, attends to useful ones, and predicts the next token."),
        ("explain attention simply", "Attention is like asking: which previous words matter most right now?"),
        ("what should i learn first", "First learn token embeddings, positional embeddings, causal attention, and next-token prediction."),
        ("how are you", "I am running as a tiny Transformer example."),
        ("thank you", "You are welcome."),
        ("bye", "Goodbye. Keep learning Transformers step by step."),
    ]

    conversations = []

    for user_text, bot_text in pairs:
        conversations.append(
            f"User: {user_text}\n"
            f"Bot: {bot_text}\n"
        )

    text = "\n".join(conversations)

    # Repeat for easy educational learning.
    text = text * 200

    return text


# ============================================================
# 4. Character Tokenizer
# ============================================================

class CharTokenizer:
    def __init__(self):
        chars = list(string.printable)

        if "\n" not in chars:
            chars.append("\n")

        self.itos = chars
        self.stoi = {ch: i for i, ch in enumerate(chars)}
        self.vocab_size = len(chars)

    def encode(self, text: str):
        return [self.stoi.get(ch, self.stoi["?"]) for ch in text]

    def decode(self, ids):
        return "".join(self.itos[int(i)] for i in ids)


def printable_token(ch: str) -> str:
    if ch == "\n":
        return "\\n"
    if ch == "\t":
        return "\\t"
    if ch == " ":
        return "<space>"
    if ch == "\r":
        return "\\r"
    if ch == "\x0b":
        return "\\x0b"
    if ch == "\x0c":
        return "\\x0c"
    return ch


def clean_text_for_plot(text: str) -> str:
    cleaned = []

    for ch in text:
        if ch in "\n\t":
            cleaned.append(ch)
        elif ch in string.printable and ch not in "\x0b\x0c\r":
            cleaned.append(ch)
        else:
            cleaned.append(" ")

    return "".join(cleaned)


# ============================================================
# 5. Transformer Components
# ============================================================

class CausalSelfAttention(nn.Module):
    def __init__(self):
        super().__init__()

        assert N_EMBD % N_HEAD == 0

        self.n_head = N_HEAD
        self.head_dim = N_EMBD // N_HEAD

        self.qkv_proj = nn.Linear(N_EMBD, 3 * N_EMBD)
        self.out_proj = nn.Linear(N_EMBD, N_EMBD)

        self.attn_dropout = nn.Dropout(DROPOUT)
        self.resid_dropout = nn.Dropout(DROPOUT)

        mask = torch.tril(torch.ones(BLOCK_SIZE, BLOCK_SIZE))

        self.register_buffer(
            "causal_mask",
            mask.view(1, 1, BLOCK_SIZE, BLOCK_SIZE)
        )

    def forward(self, x, return_attention=False):
        B, T, C = x.shape

        qkv = self.qkv_proj(x)
        q, k, v = qkv.split(C, dim=2)

        q = q.view(B, T, self.n_head, self.head_dim).transpose(1, 2)
        k = k.view(B, T, self.n_head, self.head_dim).transpose(1, 2)
        v = v.view(B, T, self.n_head, self.head_dim).transpose(1, 2)

        # Core attention equation:
        #   Attention score = Q K^T / sqrt(d_head)
        att = (q @ k.transpose(-2, -1)) / math.sqrt(self.head_dim)

        # Causal mask:
        #   token t cannot see future tokens.
        att = att.masked_fill(
            self.causal_mask[:, :, :T, :T] == 0,
            float("-inf")
        )

        att = F.softmax(att, dim=-1)

        att_for_visual = att.detach()

        att = self.attn_dropout(att)

        y = att @ v

        y = y.transpose(1, 2).contiguous().view(B, T, C)

        y = self.out_proj(y)
        y = self.resid_dropout(y)

        if return_attention:
            return y, att_for_visual

        return y, None


class FeedForward(nn.Module):
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
            idx = idx[:, -BLOCK_SIZE:]
            B, T = idx.shape

        positions = torch.arange(0, T, device=idx.device)

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
                logits.reshape(B * T, V),
                targets.reshape(B * T)
            )

        if return_attention:
            return logits, loss, attention_maps

        return logits, loss

    @torch.no_grad()
    def generate_greedy(self, idx, max_new_tokens=90):
        self.eval()

        for _ in range(max_new_tokens):
            idx_cond = idx[:, -BLOCK_SIZE:]

            logits, _ = self(idx_cond)

            logits = logits[:, -1, :]

            next_id = torch.argmax(
                logits,
                dim=-1,
                keepdim=True
            )

            idx = torch.cat([idx, next_id], dim=1)

            # Stop if newline generated after answer begins.
            if int(next_id.item()) == tokenizer.stoi["\n"]:
                break

        return idx


# ============================================================
# 6. Batching
# ============================================================

def get_batch(data_ids: torch.Tensor):
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
# 7. Probe / Microscope Functions
# ============================================================

@torch.no_grad()
def get_next_token_candidates(model, tokenizer, prompt: str, top_k: int):
    """
    Show next-token probabilities after a fixed prompt.

    Example:
        prompt = "User: what is transformer\nBot:"

    Correct next character should be:
        space
    """

    model.eval()

    ids = tokenizer.encode(prompt)

    idx = torch.tensor(
        [ids],
        dtype=torch.long,
        device=DEVICE
    )

    logits, _ = model(idx)

    logits = logits[:, -1, :]
    probs = F.softmax(logits, dim=-1)

    top_probs, top_ids = torch.topk(
        probs,
        k=min(top_k, probs.size(-1)),
        dim=-1
    )

    top_probs = top_probs[0].detach().cpu().numpy()
    top_ids = top_ids[0].detach().cpu().numpy()

    tokens = []
    token_prints = []

    for token_id in top_ids:
        ch = tokenizer.decode([int(token_id)])
        tokens.append(ch)
        token_prints.append(printable_token(ch))

    return top_ids.astype(np.int32), tokens, token_prints, top_probs.astype(np.float32)


@torch.no_grad()
def get_correct_token_probability_curve(model, tokenizer):
    """
    For the full probe sequence:
        User: what is transformer
        Bot: A Transformer is a neural network based on attention.

    Compute probability assigned to the correct next character
    at every position.

    If training works, these probabilities increase over epochs.
    """

    model.eval()

    full_text = PROBE_PROMPT + PROBE_TARGET_ANSWER

    ids = tokenizer.encode(full_text)

    x_ids = ids[:-1]
    y_ids = ids[1:]

    x = torch.tensor(
        [x_ids],
        dtype=torch.long,
        device=DEVICE
    )

    y = torch.tensor(
        [y_ids],
        dtype=torch.long,
        device=DEVICE
    )

    logits, loss = model(x, y)

    probs = F.softmax(logits, dim=-1)

    T = y.shape[1]
    pos = torch.arange(T, device=DEVICE)

    correct_probs = probs[0, pos, y[0]]

    correct_probs_np = correct_probs.detach().cpu().numpy().astype(np.float32)

    mean_correct_prob = float(correct_probs.mean().item())
    probe_loss = float(loss.item())

    return correct_probs_np, mean_correct_prob, probe_loss


@torch.no_grad()
def generate_probe_answer(model, tokenizer):
    model.eval()

    ids = tokenizer.encode(PROBE_PROMPT)

    idx = torch.tensor(
        [ids],
        dtype=torch.long,
        device=DEVICE
    )

    out = model.generate_greedy(
        idx,
        max_new_tokens=MAX_NEW_TOKENS
    )

    full_text = tokenizer.decode(out[0].detach().cpu().tolist())

    answer = full_text[len(PROBE_PROMPT):]

    if "\nUser:" in answer:
        answer = answer.split("\nUser:")[0]

    answer = clean_text_for_plot(answer)

    if len(answer.strip()) == 0:
        answer = "(empty / still random)"

    return answer


@torch.no_grad()
def get_attention_map(model, tokenizer):
    """
    Visualize final-layer head-0 attention on the fixed prompt.

    Shape:
        [T_prompt, T_prompt]
    """

    model.eval()

    ids = tokenizer.encode(PROBE_PROMPT)

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

    attn = attention_maps[-1][0, 0]

    return attn.detach().cpu().numpy().astype(np.float32)


# ============================================================
# 8. Setup
# ============================================================

tokenizer = CharTokenizer()

text = build_training_text()

all_ids = torch.tensor(
    tokenizer.encode(text),
    dtype=torch.long
)

split_idx = int(0.9 * len(all_ids))

train_ids = all_ids[:split_idx]
val_ids = all_ids[split_idx:]

model = TinyTransformerChatbot(
    vocab_size=tokenizer.vocab_size
).to(DEVICE)

optimizer = torch.optim.AdamW(
    model.parameters(),
    lr=LR,
    weight_decay=0.01
)

print(f"Using device: {DEVICE}")
print(f"Fixed probe prompt:")
print(PROBE_PROMPT)
print(f"Correct target answer:")
print(PROBE_TARGET_ANSWER)
print("Start training...\n")


# ============================================================
# 9. Training + Save Trace
# ============================================================

train_losses = []
val_losses = []

saved_epochs = []

generated_answers = []
candidate_token_ids_history = []
candidate_token_prints_history = []
candidate_probs_history = []

correct_prob_history = []
mean_correct_prob_history = []
probe_loss_history = []

attention_history = []

for epoch in range(NUM_EPOCHS + 1):

    # Save random initial model at epoch 0.
    if epoch > 0:
        model.train()

        x, y = get_batch(train_ids)

        _, loss = model(x, y)

        optimizer.zero_grad(set_to_none=True)
        loss.backward()
        optimizer.step()

    train_loss, val_loss = estimate_loss(
        model,
        train_ids,
        val_ids
    )

    train_losses.append(train_loss)
    val_losses.append(val_loss)

    if epoch % SAVE_EVERY == 0:
        answer = generate_probe_answer(model, tokenizer)

        token_ids, tokens, token_prints, token_probs = get_next_token_candidates(
            model=model,
            tokenizer=tokenizer,
            prompt=PROBE_PROMPT,
            top_k=TOP_K
        )

        correct_probs, mean_correct_prob, probe_loss = get_correct_token_probability_curve(
            model,
            tokenizer
        )

        attn = get_attention_map(model, tokenizer)

        saved_epochs.append(epoch)
        generated_answers.append(answer)

        candidate_token_ids_history.append(token_ids)
        candidate_token_prints_history.append(token_prints)
        candidate_probs_history.append(token_probs)

        correct_prob_history.append(correct_probs)
        mean_correct_prob_history.append(mean_correct_prob)
        probe_loss_history.append(probe_loss)

        attention_history.append(attn)

    if epoch % 100 == 0:
        print(
            f"Epoch {epoch:5d}/{NUM_EPOCHS} | "
            f"Train Loss: {train_losses[-1]:.6f} | "
            f"Val Loss: {val_losses[-1]:.6f}"
        )


saved_epochs = np.array(saved_epochs, dtype=np.int32)
train_losses = np.array(train_losses, dtype=np.float32)
val_losses = np.array(val_losses, dtype=np.float32)

candidate_token_ids_history = np.stack(candidate_token_ids_history, axis=0).astype(np.int32)
candidate_probs_history = np.stack(candidate_probs_history, axis=0).astype(np.float32)

correct_prob_history = np.stack(correct_prob_history, axis=0).astype(np.float32)
mean_correct_prob_history = np.array(mean_correct_prob_history, dtype=np.float32)
probe_loss_history = np.array(probe_loss_history, dtype=np.float32)

attention_history = np.stack(attention_history, axis=0).astype(np.float32)

np.savez(
    NPZ_NAME,
    saved_epochs=saved_epochs,
    train_losses=train_losses,
    val_losses=val_losses,
    generated_answers=np.array(generated_answers, dtype=object),
    candidate_token_ids_history=candidate_token_ids_history,
    candidate_token_prints_history=np.array(candidate_token_prints_history, dtype=object),
    candidate_probs_history=candidate_probs_history,
    correct_prob_history=correct_prob_history,
    mean_correct_prob_history=mean_correct_prob_history,
    probe_loss_history=probe_loss_history,
    attention_history=attention_history,
    probe_prompt=PROBE_PROMPT,
    probe_target_answer=PROBE_TARGET_ANSWER,
    top_k=TOP_K,
    num_epochs=NUM_EPOCHS,
    save_every=SAVE_EVERY,
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
# 10. Render Video
# ============================================================

print("Start rendering video...")

fig = plt.figure(figsize=(7, 12))

ax_text = fig.add_axes([0.07, 0.76, 0.86, 0.18])
ax_bar = fig.add_axes([0.18, 0.56, 0.72, 0.15])
ax_correct = fig.add_axes([0.10, 0.37, 0.82, 0.13])
ax_attn = fig.add_axes([0.16, 0.17, 0.68, 0.14])
ax_loss = fig.add_axes([0.10, 0.05, 0.82, 0.08])

metadata = dict(
    title="Transformer Learning Microscope"
)

writer = FFMpegWriter(
    fps=VIDEO_FPS,
    metadata=metadata
)

target_next_char = PROBE_TARGET_ANSWER[0]
target_next_print = printable_token(target_next_char)

with writer.saving(fig, VIDEO_NAME, dpi=160):

    for frame_idx, epoch in enumerate(saved_epochs):

        ax_text.clear()
        ax_bar.clear()
        ax_correct.clear()
        ax_attn.clear()
        ax_loss.clear()

        answer = generated_answers[frame_idx]

        candidate_labels = candidate_token_prints_history[frame_idx]
        candidate_probs = candidate_probs_history[frame_idx] * 100.0
        candidate_ids = candidate_token_ids_history[frame_idx]

        correct_probs = correct_prob_history[frame_idx]
        mean_correct_prob = mean_correct_prob_history[frame_idx]
        probe_loss = probe_loss_history[frame_idx]

        attn = attention_history[frame_idx]

        # ----------------------------------------------------
        # Text panel
        # ----------------------------------------------------
        ax_text.axis("off")

        wrapped_answer = textwrap.fill(
            answer,
            width=68
        )

        target_answer_clean = clean_text_for_plot(PROBE_TARGET_ANSWER.strip())

        text_panel = (
            "Transformer Learning Microscope\n\n"
            f"Fixed prompt:\n{PROBE_PROMPT}\n\n"
            f"Generated answer at epoch {epoch}:\n"
            f"{wrapped_answer}\n\n"
            f"Target answer:\n{target_answer_clean}"
        )

        ax_text.text(
            0.0,
            1.0,
            text_panel,
            transform=ax_text.transAxes,
            va="top",
            ha="left",
            fontsize=10,
            family="monospace",
            bbox=dict(
                boxstyle="round,pad=0.55",
                facecolor="white",
                alpha=0.95,
            ),
        )

        ax_text.set_title(
            "Why Transformer Training Works",
            fontsize=17,
            fontweight="bold",
            pad=12,
        )

        # ----------------------------------------------------
        # Next-token probability bar chart
        # ----------------------------------------------------
        labels_plot = candidate_labels[::-1]
        probs_plot = candidate_probs[::-1]
        ids_plot = candidate_ids[::-1]

        target_id = tokenizer.stoi[target_next_char]

        colors = []

        for tid in ids_plot:
            if int(tid) == int(target_id):
                colors.append("tab:orange")
            else:
                colors.append("tab:blue")

        y_pos = np.arange(len(labels_plot))

        ax_bar.barh(
            y_pos,
            probs_plot,
            color=colors,
            alpha=0.88
        )

        ax_bar.set_yticks(y_pos)
        ax_bar.set_yticklabels(labels_plot, fontsize=8)

        ax_bar.set_xlabel("probability [%]")
        ax_bar.set_title(
            f"Next-token candidates after prompt | correct next token = '{target_next_print}'",
            fontsize=11,
            fontweight="bold"
        )

        xmax = max(1.0, float(np.max(probs_plot)) * 1.2)

        ax_bar.set_xlim(0, xmax)
        ax_bar.grid(True, axis="x", alpha=0.3)

        for y, p in zip(y_pos, probs_plot):
            ax_bar.text(
                p + xmax * 0.01,
                y,
                f"{p:.2f}%",
                va="center",
                fontsize=7,
            )

        # ----------------------------------------------------
        # Correct token probability curve
        # ----------------------------------------------------
        pos_axis = np.arange(len(correct_probs))

        ax_correct.plot(
            pos_axis,
            correct_probs,
            linewidth=1.7,
            label="P(correct next character)"
        )

        ax_correct.set_ylim(0.0, 1.05)
        ax_correct.set_xlim(0, len(correct_probs) - 1)

        ax_correct.set_xlabel("position in probe sequence")
        ax_correct.set_ylabel("probability")

        ax_correct.set_title(
            "Correct Next-Character Probability Across the Whole Answer",
            fontsize=11,
            fontweight="bold"
        )

        ax_correct.grid(True, alpha=0.3)

        ax_correct.text(
            0.98,
            0.15,
            f"mean P(correct) = {mean_correct_prob:.4f}\nprobe CE loss = {probe_loss:.4f}",
            transform=ax_correct.transAxes,
            va="bottom",
            ha="right",
            fontsize=8,
            bbox=dict(
                boxstyle="round,pad=0.35",
                facecolor="white",
                alpha=0.9,
            ),
        )

        # ----------------------------------------------------
        # Attention heatmap
        # ----------------------------------------------------
        ax_attn.imshow(
            attn,
            aspect="auto",
            origin="lower"
        )

        ax_attn.set_title(
            "Causal Self-Attention Heatmap | Last Layer, Head 0",
            fontsize=11,
            fontweight="bold"
        )

        ax_attn.set_xlabel("key token position")
        ax_attn.set_ylabel("query token position")

        ax_attn.text(
            0.02,
            0.94,
            "lower-triangular = no future-token access",
            transform=ax_attn.transAxes,
            va="top",
            ha="left",
            fontsize=7,
            bbox=dict(
                boxstyle="round,pad=0.3",
                facecolor="white",
                alpha=0.85,
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
            linewidth=1.5,
        )

        ax_loss.plot(
            epoch_axis[:epoch + 1],
            val_losses[:epoch + 1],
            label="Validation Loss",
            linewidth=1.5,
        )

        ax_loss.scatter(
            [epoch],
            [val_losses[epoch]],
            s=20,
        )

        ax_loss.set_xlim(0, NUM_EPOCHS)

        max_loss_for_plot = max(
            float(np.max(train_losses[:min(200, len(train_losses))])),
            float(np.max(val_losses[:min(200, len(val_losses))])),
        )

        ax_loss.set_ylim(0.0, max_loss_for_plot * 1.05)

        ax_loss.set_xlabel("epoch")
        ax_loss.set_ylabel("CE loss")

        ax_loss.grid(True, alpha=0.3)
        ax_loss.legend(loc="upper right", fontsize=7)

        ax_loss.text(
            0.02,
            0.84,
            f"epoch = {epoch}/{NUM_EPOCHS}",
            transform=ax_loss.transAxes,
            va="top",
            ha="left",
            fontsize=8,
            bbox=dict(
                boxstyle="round,pad=0.3",
                facecolor="white",
                alpha=0.85,
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
