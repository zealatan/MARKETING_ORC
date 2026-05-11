
import os
import math
import string
import argparse
import textwrap
from dataclasses import dataclass

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

@dataclass
class Config:
    block_size: int = 128
    n_embd: int = 128
    n_head: int = 4
    n_layer: int = 4
    dropout: float = 0.1


OUT_DIR = "token_choice_visual_out"
os.makedirs(OUT_DIR, exist_ok=True)

VIDEO_NAME = os.path.join(
    OUT_DIR,
    "transformer_token_choice_dynamic.mp4"
)

NPZ_NAME = os.path.join(
    OUT_DIR,
    "token_choice_trace.npz"
)

SEED = 0
VIDEO_FPS = 2

DEVICE = "cuda" if torch.cuda.is_available() else "cpu"


# ============================================================
# 2. Reproducibility
# ============================================================

torch.manual_seed(SEED)
np.random.seed(SEED)

if DEVICE == "cuda":
    torch.cuda.manual_seed_all(SEED)


# ============================================================
# 3. Character tokenizer
# ============================================================

class CharTokenizer:
    def __init__(self, vocab=None):
        if vocab is None:
            chars = list(string.printable)

            if "\n" not in chars:
                chars.append("\n")

            self.itos = chars
        else:
            self.itos = vocab

        self.stoi = {
            ch: i
            for i, ch in enumerate(self.itos)
        }

        self.vocab_size = len(self.itos)

    def encode(self, text: str):
        return [
            self.stoi.get(ch, self.stoi.get("?", 0))
            for ch in text
        ]

    def decode(self, ids):
        return "".join(
            self.itos[int(i)]
            for i in ids
        )


def printable_token(ch: str) -> str:
    """
    Make character tokens readable in plots.
    """

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
    if ch == "":
        return "<empty>"

    return ch


def clean_for_plot(text: str) -> str:
    """
    Remove control characters that can break matplotlib text rendering.
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


# ============================================================
# 4. Transformer model
# ============================================================

class CausalSelfAttention(nn.Module):
    def __init__(self, cfg: Config):
        super().__init__()

        assert cfg.n_embd % cfg.n_head == 0

        self.cfg = cfg
        self.n_head = cfg.n_head
        self.head_dim = cfg.n_embd // cfg.n_head

        self.qkv_proj = nn.Linear(
            cfg.n_embd,
            3 * cfg.n_embd
        )

        self.out_proj = nn.Linear(
            cfg.n_embd,
            cfg.n_embd
        )

        self.attn_dropout = nn.Dropout(cfg.dropout)
        self.resid_dropout = nn.Dropout(cfg.dropout)

        mask = torch.tril(
            torch.ones(
                cfg.block_size,
                cfg.block_size
            )
        )

        self.register_buffer(
            "causal_mask",
            mask.view(
                1,
                1,
                cfg.block_size,
                cfg.block_size
            )
        )

    def forward(self, x):
        B, T, C = x.shape

        qkv = self.qkv_proj(x)

        q, k, v = qkv.split(C, dim=2)

        q = q.view(
            B,
            T,
            self.n_head,
            self.head_dim
        ).transpose(1, 2)

        k = k.view(
            B,
            T,
            self.n_head,
            self.head_dim
        ).transpose(1, 2)

        v = v.view(
            B,
            T,
            self.n_head,
            self.head_dim
        ).transpose(1, 2)

        # ----------------------------------------------------
        # Core Transformer attention score
        # ----------------------------------------------------
        att = (
            q @ k.transpose(-2, -1)
        ) / math.sqrt(self.head_dim)

        # ----------------------------------------------------
        # Causal mask:
        # current token cannot see future tokens.
        # ----------------------------------------------------
        att = att.masked_fill(
            self.causal_mask[:, :, :T, :T] == 0,
            float("-inf")
        )

        att = F.softmax(att, dim=-1)
        att = self.attn_dropout(att)

        y = att @ v

        y = y.transpose(
            1,
            2
        ).contiguous().view(B, T, C)

        y = self.out_proj(y)
        y = self.resid_dropout(y)

        return y


class FeedForward(nn.Module):
    def __init__(self, cfg: Config):
        super().__init__()

        self.net = nn.Sequential(
            nn.Linear(cfg.n_embd, 4 * cfg.n_embd),
            nn.GELU(),
            nn.Linear(4 * cfg.n_embd, cfg.n_embd),
            nn.Dropout(cfg.dropout),
        )

    def forward(self, x):
        return self.net(x)


class TransformerBlock(nn.Module):
    def __init__(self, cfg: Config):
        super().__init__()

        self.ln1 = nn.LayerNorm(cfg.n_embd)
        self.attn = CausalSelfAttention(cfg)

        self.ln2 = nn.LayerNorm(cfg.n_embd)
        self.ff = FeedForward(cfg)

    def forward(self, x):
        x = x + self.attn(self.ln1(x))
        x = x + self.ff(self.ln2(x))

        return x


class TinyTransformerChatbot(nn.Module):
    def __init__(self, cfg: Config, vocab_size: int):
        super().__init__()

        self.cfg = cfg
        self.vocab_size = vocab_size

        self.token_emb = nn.Embedding(
            vocab_size,
            cfg.n_embd
        )

        self.pos_emb = nn.Embedding(
            cfg.block_size,
            cfg.n_embd
        )

        self.blocks = nn.ModuleList([
            TransformerBlock(cfg)
            for _ in range(cfg.n_layer)
        ])

        self.ln_f = nn.LayerNorm(cfg.n_embd)
        self.lm_head = nn.Linear(
            cfg.n_embd,
            vocab_size
        )

    def forward(self, idx):
        B, T = idx.shape

        if T > self.cfg.block_size:
            idx = idx[:, -self.cfg.block_size:]
            B, T = idx.shape

        positions = torch.arange(
            0,
            T,
            device=idx.device
        )

        tok = self.token_emb(idx)
        pos = self.pos_emb(positions)

        x = tok + pos

        for block in self.blocks:
            x = block(x)

        x = self.ln_f(x)

        logits = self.lm_head(x)

        return logits


# ============================================================
# 5. Checkpoint loading
# ============================================================

def safe_torch_load(path: str, device: str):
    try:
        return torch.load(
            path,
            map_location=device,
            weights_only=False
        )
    except TypeError:
        return torch.load(
            path,
            map_location=device
        )


def load_model(ckpt_path: str):
    ckpt = safe_torch_load(
        ckpt_path,
        DEVICE
    )

    cfg_dict = ckpt.get("config", {})

    cfg = Config(
        block_size=cfg_dict.get("block_size", 128),
        n_embd=cfg_dict.get("n_embd", 128),
        n_head=cfg_dict.get("n_head", 4),
        n_layer=cfg_dict.get("n_layer", 4),
        dropout=cfg_dict.get("dropout", 0.1),
    )

    tokenizer = CharTokenizer(
        vocab=ckpt["vocab"]
    )

    model = TinyTransformerChatbot(
        cfg=cfg,
        vocab_size=tokenizer.vocab_size
    ).to(DEVICE)

    model.load_state_dict(
        ckpt["model_state_dict"]
    )

    model.eval()

    print(f"[INFO] Loaded checkpoint: {ckpt_path}")
    print(f"[INFO] Device: {DEVICE}")
    print(f"[INFO] Vocab size: {tokenizer.vocab_size}")
    print(
        "[INFO] "
        f"block_size={cfg.block_size}, "
        f"n_embd={cfg.n_embd}, "
        f"n_head={cfg.n_head}, "
        f"n_layer={cfg.n_layer}"
    )

    return model, tokenizer


# ============================================================
# 6. Token probability + token selection
# ============================================================

@torch.no_grad()
def get_next_token_distribution(
    model,
    idx,
    temperature: float,
):
    """
    Returns probability distribution over next token.

    idx:
        [1, T]

    Output:
        probs:
            [1, vocab_size]
    """

    idx_cond = idx[:, -model.cfg.block_size:]

    logits = model(idx_cond)

    # Only the last position predicts the next token.
    logits = logits[:, -1, :]

    # Temperature controls distribution sharpness.
    logits = logits / temperature

    probs = F.softmax(logits, dim=-1)

    return probs


@torch.no_grad()
def choose_token(
    probs,
    decode_mode: str,
    sample_top_k: int,
):
    """
    Choose next token from probability distribution.

    decode_mode:
        greedy:
            choose highest-probability token

        sample:
            sample randomly from top-k probability mass
    """

    if decode_mode == "greedy":
        next_id = torch.argmax(
            probs,
            dim=-1,
            keepdim=True
        )

        return next_id

    if decode_mode == "sample":
        top_probs, top_ids = torch.topk(
            probs,
            k=min(sample_top_k, probs.size(-1)),
            dim=-1
        )

        top_probs = top_probs / top_probs.sum(
            dim=-1,
            keepdim=True
        )

        sampled_pos = torch.multinomial(
            top_probs,
            num_samples=1
        )

        next_id = top_ids.gather(
            dim=-1,
            index=sampled_pos
        )

        return next_id

    raise ValueError(
        f"Unsupported decode mode: {decode_mode}"
    )


@torch.no_grad()
def get_topk_candidates(
    probs,
    tokenizer,
    top_k: int,
):
    top_probs, top_ids = torch.topk(
        probs,
        k=min(top_k, probs.size(-1)),
        dim=-1
    )

    top_probs = top_probs[0].detach().cpu()
    top_ids = top_ids[0].detach().cpu()

    candidates = []

    for prob, token_id in zip(top_probs, top_ids):
        token_id_int = int(token_id.item())
        token = tokenizer.decode([token_id_int])

        candidates.append(
            {
                "token_id": token_id_int,
                "token": token,
                "token_print": printable_token(token),
                "prob": float(prob.item()),
            }
        )

    return candidates


# ============================================================
# 7. Build token-choice trace
# ============================================================

@torch.no_grad()
def build_token_choice_trace(
    model,
    tokenizer,
    user_prompt: str,
    max_new_tokens: int,
    temperature: float,
    top_k: int,
    decode_mode: str,
    sample_top_k: int,
):
    """
    Generate answer step-by-step and save all token decisions.
    """

    prompt = f"User: {user_prompt}\nBot:"

    ids = tokenizer.encode(prompt)

    idx = torch.tensor(
        [ids],
        dtype=torch.long,
        device=DEVICE
    )

    generated_tokens = []
    trace = []

    for step in range(max_new_tokens):
        answer_before = "".join(generated_tokens)

        probs = get_next_token_distribution(
            model=model,
            idx=idx,
            temperature=temperature
        )

        candidates = get_topk_candidates(
            probs=probs,
            tokenizer=tokenizer,
            top_k=top_k
        )

        next_id = choose_token(
            probs=probs,
            decode_mode=decode_mode,
            sample_top_k=sample_top_k
        )

        next_id_int = int(next_id.item())
        chosen_token = tokenizer.decode([next_id_int])
        chosen_token_print = printable_token(chosen_token)

        chosen_prob = float(
            probs[0, next_id_int].detach().cpu().item()
        )

        generated_tokens.append(chosen_token)

        answer_after = "".join(generated_tokens)

        trace.append(
            {
                "step": step,
                "prompt": prompt,
                "answer_before": answer_before,
                "answer_after": answer_after,
                "chosen_token_id": next_id_int,
                "chosen_token": chosen_token,
                "chosen_token_print": chosen_token_print,
                "chosen_prob": chosen_prob,
                "candidates": candidates,
            }
        )

        idx = torch.cat(
            [idx, next_id],
            dim=1
        )

        # Stop condition for toy chatbot.
        if "\nUser:" in answer_after:
            break

        if chosen_token == "\n" and len(answer_after.strip()) > 0:
            break

    return trace


# ============================================================
# 8. Save trace as NPZ
# ============================================================

def save_trace_npz(trace, user_prompt, temperature, top_k, decode_mode):
    steps = []
    chosen_ids = []
    chosen_tokens = []
    chosen_probs = []
    answer_after = []

    for item in trace:
        steps.append(item["step"])
        chosen_ids.append(item["chosen_token_id"])
        chosen_tokens.append(item["chosen_token_print"])
        chosen_probs.append(item["chosen_prob"])
        answer_after.append(item["answer_after"])

    np.savez(
        NPZ_NAME,
        steps=np.array(steps, dtype=np.int32),
        chosen_ids=np.array(chosen_ids, dtype=np.int32),
        chosen_tokens=np.array(chosen_tokens, dtype=object),
        chosen_probs=np.array(chosen_probs, dtype=np.float32),
        answer_after=np.array(answer_after, dtype=object),
        user_prompt=user_prompt,
        temperature=temperature,
        top_k=top_k,
        decode_mode=decode_mode,
    )

    print(f"[INFO] Saved trace: {NPZ_NAME}")


# ============================================================
# 9. Render token-choice video
# ============================================================

def render_video(
    trace,
    user_prompt: str,
    temperature: float,
    top_k: int,
    decode_mode: str,
):
    print("[INFO] Start rendering video...")

    # Vertical 1080x1920 style.
    fig = plt.figure(figsize=(6, 10.67))

    ax_text = fig.add_axes([0.08, 0.61, 0.84, 0.31])
    ax_bar = fig.add_axes([0.20, 0.27, 0.68, 0.27])
    ax_info = fig.add_axes([0.08, 0.08, 0.84, 0.13])

    metadata = dict(
        title="Transformer Token Choice Visualization"
    )

    writer = FFMpegWriter(
        fps=VIDEO_FPS,
        metadata=metadata
    )

    with writer.saving(fig, VIDEO_NAME, dpi=180):

        for item in trace:
            ax_text.clear()
            ax_bar.clear()
            ax_info.clear()

            step = item["step"]
            prompt = item["prompt"]

            answer_before = clean_for_plot(
                item["answer_before"]
            )

            answer_after = clean_for_plot(
                item["answer_after"]
            )

            chosen_token_print = item["chosen_token_print"]
            chosen_prob = item["chosen_prob"]

            candidates = item["candidates"]

            # ------------------------------------------------
            # Text panel
            # ------------------------------------------------
            ax_text.axis("off")

            answer_before_wrapped = textwrap.fill(
                answer_before if answer_before else "(empty)",
                width=48
            )

            answer_after_wrapped = textwrap.fill(
                answer_after if answer_after else "(empty)",
                width=48
            )

            panel_text = (
                "Transformer Token Selection Process\n\n"
                f"Prompt:\n{prompt}\n\n"
                f"Answer before choosing token:\n"
                f"{answer_before_wrapped}\n\n"
                f"Chosen token at step {step}:\n"
                f"'{chosen_token_print}' "
                f"with probability {chosen_prob * 100.0:.3f}%\n\n"
                f"Answer after choosing token:\n"
                f"{answer_after_wrapped}"
            )

            ax_text.text(
                0.0,
                1.0,
                panel_text,
                transform=ax_text.transAxes,
                va="top",
                ha="left",
                fontsize=10,
                family="monospace",
                bbox=dict(
                    boxstyle="round,pad=0.6",
                    facecolor="white",
                    alpha=0.94,
                ),
            )

            ax_text.set_title(
                "How a Transformer Chatbot Chooses the Next Token",
                fontsize=16,
                fontweight="bold",
                pad=14,
            )

            # ------------------------------------------------
            # Probability bar chart
            # ------------------------------------------------
            labels = [
                c["token_print"]
                for c in candidates
            ]

            probs_percent = np.array([
                c["prob"] * 100.0
                for c in candidates
            ], dtype=np.float32)

            token_ids = [
                c["token_id"]
                for c in candidates
            ]

            chosen_id = item["chosen_token_id"]

            # Reverse order so highest probability appears at top.
            labels_plot = labels[::-1]
            probs_plot = probs_percent[::-1]
            token_ids_plot = token_ids[::-1]

            colors = []

            for tid in token_ids_plot:
                if tid == chosen_id:
                    colors.append("tab:orange")
                else:
                    colors.append("tab:blue")

            y_pos = np.arange(len(labels_plot))

            ax_bar.barh(
                y_pos,
                probs_plot,
                color=colors,
                alpha=0.88,
            )

            ax_bar.set_yticks(y_pos)
            ax_bar.set_yticklabels(
                labels_plot,
                fontsize=9
            )

            ax_bar.set_xlabel("next-token probability [%]")
            ax_bar.set_title(
                f"Top-{top_k} Candidate Tokens Before Selection",
                fontsize=12,
                fontweight="bold"
            )

            xmax = max(
                1.0,
                float(np.max(probs_percent)) * 1.20
            )

            ax_bar.set_xlim(0, xmax)
            ax_bar.grid(True, axis="x", alpha=0.3)

            for y, p in zip(y_pos, probs_plot):
                ax_bar.text(
                    p + xmax * 0.01,
                    y,
                    f"{p:.2f}%",
                    va="center",
                    fontsize=8,
                )

            # ------------------------------------------------
            # Info panel
            # ------------------------------------------------
            ax_info.axis("off")

            info_text = (
                f"Prompt question: {user_prompt}\n"
                f"Decode mode: {decode_mode} | "
                f"temperature: {temperature} | "
                f"display top-k: {top_k}\n\n"
                "Generation rule:\n"
                "context -> Transformer -> logits -> softmax probabilities "
                "-> choose one token -> append -> repeat"
            )

            ax_info.text(
                0.0,
                1.0,
                info_text,
                transform=ax_info.transAxes,
                va="top",
                ha="left",
                fontsize=10,
                family="monospace",
                bbox=dict(
                    boxstyle="round,pad=0.55",
                    facecolor="white",
                    alpha=0.92,
                ),
            )

            writer.grab_frame()

        # Hold final frame.
        final_hold_frames = VIDEO_FPS * 3

        for _ in range(final_hold_frames):
            writer.grab_frame()

    plt.close(fig)

    print(f"[INFO] Saved video: {VIDEO_NAME}")


# ============================================================
# 10. Main
# ============================================================

def main():
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--ckpt",
        type=str,
        default="training_video_out_transformer/tiny_transformer_chatbot.pt",
        help="Path to trained tiny Transformer chatbot checkpoint"
    )

    parser.add_argument(
        "--prompt",
        type=str,
        default="what is transformer",
        help="User prompt to visualize"
    )

    parser.add_argument(
        "--max-new-tokens",
        type=int,
        default=80,
        help="Maximum generated character tokens"
    )

    parser.add_argument(
        "--temperature",
        type=float,
        default=0.8,
        help="Sampling temperature"
    )

    parser.add_argument(
        "--top-k",
        type=int,
        default=10,
        help="Number of candidate tokens to visualize"
    )

    parser.add_argument(
        "--decode",
        type=str,
        default="greedy",
        choices=["greedy", "sample"],
        help="Token choice method"
    )

    parser.add_argument(
        "--sample-top-k",
        type=int,
        default=10,
        help="For sample mode, sample only from top-k tokens"
    )

    args = parser.parse_args()

    model, tokenizer = load_model(args.ckpt)

    trace = build_token_choice_trace(
        model=model,
        tokenizer=tokenizer,
        user_prompt=args.prompt,
        max_new_tokens=args.max_new_tokens,
        temperature=args.temperature,
        top_k=args.top_k,
        decode_mode=args.decode,
        sample_top_k=args.sample_top_k,
    )

    save_trace_npz(
        trace=trace,
        user_prompt=args.prompt,
        temperature=args.temperature,
        top_k=args.top_k,
        decode_mode=args.decode,
    )

    render_video(
        trace=trace,
        user_prompt=args.prompt,
        temperature=args.temperature,
        top_k=args.top_k,
        decode_mode=args.decode,
    )

    final_answer = trace[-1]["answer_after"].strip()

    print("\n============================================================")
    print("Final generated answer")
    print("============================================================")
    print(final_answer)
    print("")
    print("Open video:")
    print(f"firefox {VIDEO_NAME}")


if __name__ == "__main__":
    main()
