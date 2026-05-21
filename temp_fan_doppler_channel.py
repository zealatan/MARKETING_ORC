# temp_fan_doppler_channel.py
#
# FAN-style neural network learns a complex multipath Doppler channel trajectory.
#
# Target:
#   h(t) = Σ_l a_l exp(j(2π f_D,l t + phi_l))
#
# Model input:
#   t
#
# Model output:
#   [Re{h(t)}, Im{h(t)}]
#
# This is more meaningful than y = sin(20x), because it mimics
# time-varying complex wireless channel behavior.
#
# Output:
#   training_video_out_fan_doppler/
#     ├── fan_doppler_channel_trace.npz
#     └── fan_doppler_channel_dynamic.mp4
#
# Run:
#   python3 temp_fan_doppler_channel.py
#
# Open:
#   firefox training_video_out_fan_doppler/fan_doppler_channel_dynamic.mp4

import os
import numpy as np
import torch
import torch.nn as nn
import matplotlib.pyplot as plt
from matplotlib.animation import FFMpegWriter


# ============================================================
# 1. Config
# ============================================================

OUT_DIR = "training_video_out_fan_doppler"
os.makedirs(OUT_DIR, exist_ok=True)

SEED = 0

NUM_EPOCHS = 4000
SAVE_EVERY = 10

LR = 5e-4

N_TRAIN = 2048
N_VAL = 2048
N_GRID = 2000

VIDEO_FPS = 30

VIDEO_NAME = os.path.join(OUT_DIR, "fan_doppler_channel_dynamic.mp4")
NPZ_NAME = os.path.join(OUT_DIR, "fan_doppler_channel_trace.npz")

DEVICE = "cuda" if torch.cuda.is_available() else "cpu"

# Time range.
# Here t is normalized time over one observation window.
T_MIN = 0.0
T_MAX = 1.0

# Plot range.
Y_MIN = -1.4
Y_MAX = 1.4


# ============================================================
# 2. Reproducibility
# ============================================================

torch.manual_seed(SEED)
np.random.seed(SEED)

if DEVICE == "cuda":
    torch.cuda.manual_seed_all(SEED)


# ============================================================
# 3. Multipath Doppler Channel Target
# ============================================================

# Normalized Doppler frequencies in cycles per observation window.
# Think of them as multiple moving paths with different Doppler shifts.
DOPPLER_FREQS = np.array([3.0, 7.0, 13.0, 21.0], dtype=np.float32)

# Path amplitudes.
PATH_AMPS = np.array([1.0, 0.55, 0.35, 0.22], dtype=np.float32)

# Path phases.
PATH_PHASES = np.array([0.2, 1.7, -0.9, 2.4], dtype=np.float32)


def target_channel_np(t: np.ndarray) -> np.ndarray:
    """
    Generate a clean complex multipath Doppler channel.

    t:
      shape [N]

    return:
      y shape [N, 2]
      y[:, 0] = Re{h(t)}
      y[:, 1] = Im{h(t)}
    """

    h = np.zeros_like(t, dtype=np.complex64)

    for amp, fd, phase in zip(PATH_AMPS, DOPPLER_FREQS, PATH_PHASES):
        h += amp * np.exp(1j * (2.0 * np.pi * fd * t + phase))

    # Normalize channel magnitude to keep values stable.
    h = h / np.sum(PATH_AMPS)

    y = np.stack(
        [
            np.real(h),
            np.imag(h),
        ],
        axis=-1,
    ).astype(np.float32)

    return y


# ============================================================
# 4. Dataset
# ============================================================

t_train = np.random.uniform(T_MIN, T_MAX, size=(N_TRAIN, 1)).astype(np.float32)
y_train = target_channel_np(t_train[:, 0])

t_val = np.random.uniform(T_MIN, T_MAX, size=(N_VAL, 1)).astype(np.float32)
y_val = target_channel_np(t_val[:, 0])

t_grid = np.linspace(T_MIN, T_MAX, N_GRID).astype(np.float32)
y_grid = target_channel_np(t_grid)

t_train_t = torch.tensor(t_train, device=DEVICE)
y_train_t = torch.tensor(y_train, device=DEVICE)

t_val_t = torch.tensor(t_val, device=DEVICE)
y_val_t = torch.tensor(y_val, device=DEVICE)

t_grid_t = torch.tensor(t_grid.reshape(-1, 1), device=DEVICE)


# ============================================================
# 5. FAN-style Layer
# ============================================================

class FANLayer(nn.Module):
    """
    Simplified FAN-style layer.

    It combines:
      1. periodic features: sin(Wp x), cos(Wp x)
      2. non-periodic features: ReLU(Wg x)
      3. output projection

    This is a compact educational implementation, not an official FAN paper implementation.
    """

    def __init__(
        self,
        in_dim: int,
        out_dim: int,
        periodic_dim: int = 64,
        nonperiodic_dim: int = 64,
    ):
        super().__init__()

        self.periodic_linear = nn.Linear(in_dim, periodic_dim)
        self.nonperiodic_linear = nn.Linear(in_dim, nonperiodic_dim)

        combined_dim = 2 * periodic_dim + nonperiodic_dim

        self.output_linear = nn.Linear(combined_dim, out_dim)
        self.activation = nn.ReLU()

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        p = self.periodic_linear(x)

        periodic_features = torch.cat(
            [
                torch.sin(p),
                torch.cos(p),
            ],
            dim=-1,
        )

        nonperiodic_features = self.activation(self.nonperiodic_linear(x))

        features = torch.cat(
            [
                periodic_features,
                nonperiodic_features,
            ],
            dim=-1,
        )

        y = self.output_linear(features)
        return y


# ============================================================
# 6. FAN-style Network
# ============================================================

class FANNet(nn.Module):
    def __init__(self):
        super().__init__()

        self.net = nn.Sequential(
            FANLayer(
                in_dim=1,
                out_dim=128,
                periodic_dim=64,
                nonperiodic_dim=64,
            ),

            nn.ReLU(),

            FANLayer(
                in_dim=128,
                out_dim=128,
                periodic_dim=64,
                nonperiodic_dim=64,
            ),

            nn.ReLU(),

            # Output:
            #   [Re{h(t)}, Im{h(t)}]
            nn.Linear(128, 2),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.net(x)


model = FANNet().to(DEVICE)

optimizer = torch.optim.Adam(model.parameters(), lr=LR)
criterion = nn.MSELoss()


# ============================================================
# 7. Training + history saving
# ============================================================

train_losses = []
val_losses = []

saved_epochs = []
pred_history = []

print(f"Using device: {DEVICE}")
print("Target: complex multipath Doppler channel h(t)")
print("Model output: [Re{h(t)}, Im{h(t)}]")
print("Start training...\n")

for epoch in range(NUM_EPOCHS + 1):

    # ----------------------------
    # Training step
    # ----------------------------
    model.train()

    optimizer.zero_grad()

    pred_train = model(t_train_t)
    loss = criterion(pred_train, y_train_t)

    loss.backward()
    optimizer.step()

    # ----------------------------
    # Evaluate updated model
    # ----------------------------
    model.eval()

    with torch.no_grad():
        train_loss_eval = criterion(model(t_train_t), y_train_t)
        val_loss_eval = criterion(model(t_val_t), y_val_t)

    train_losses.append(float(train_loss_eval.item()))
    val_losses.append(float(val_loss_eval.item()))

    # ----------------------------
    # Save prediction for video
    # ----------------------------
    if epoch % SAVE_EVERY == 0:
        with torch.no_grad():
            pred_grid = model(t_grid_t).detach().cpu().numpy()

        saved_epochs.append(epoch)
        pred_history.append(pred_grid.astype(np.float32))

    # ----------------------------
    # Print progress
    # ----------------------------
    if epoch % 100 == 0:
        print(
            f"Epoch {epoch:5d}/{NUM_EPOCHS} | "
            f"Train Loss: {train_losses[-1]:.8f} | "
            f"Val Loss: {val_losses[-1]:.8f}"
        )


saved_epochs = np.array(saved_epochs, dtype=np.int32)
pred_history = np.stack(pred_history, axis=0)

train_losses = np.array(train_losses, dtype=np.float32)
val_losses = np.array(val_losses, dtype=np.float32)

np.savez(
    NPZ_NAME,
    t_grid=t_grid,
    y_grid=y_grid,
    saved_epochs=saved_epochs,
    pred_history=pred_history,
    train_losses=train_losses,
    val_losses=val_losses,
    num_epochs=NUM_EPOCHS,
    save_every=SAVE_EVERY,
    doppler_freqs=DOPPLER_FREQS,
    path_amps=PATH_AMPS,
    path_phases=PATH_PHASES,
    t_min=T_MIN,
    t_max=T_MAX,
)

print(f"\nSaved trace to: {NPZ_NAME}")


# ============================================================
# 8. Render video
# ============================================================

print("Start rendering video...")

# Vertical reels-style format:
# 6 inch * 180 dpi = 1080 px
# 10.67 inch * 180 dpi = 1920 px
fig = plt.figure(figsize=(6, 10.67))

ax_time = fig.add_axes([0.12, 0.55, 0.82, 0.34])
ax_iq = fig.add_axes([0.18, 0.30, 0.70, 0.18])
ax_loss = fig.add_axes([0.12, 0.10, 0.82, 0.13])

metadata = dict(title="FAN-style NN Learns Multipath Doppler Channel")
writer = FFMpegWriter(fps=VIDEO_FPS, metadata=metadata)

with writer.saving(fig, VIDEO_NAME, dpi=180):

    for i, epoch in enumerate(saved_epochs):

        ax_time.clear()
        ax_iq.clear()
        ax_loss.clear()

        pred_y = pred_history[i]

        target_re = y_grid[:, 0]
        target_im = y_grid[:, 1]

        pred_re = pred_y[:, 0]
        pred_im = pred_y[:, 1]

        # ----------------------------
        # Time-domain Re/Im plot
        # ----------------------------
        ax_time.plot(
            t_grid,
            target_re,
            label="Target Re{h(t)}",
            linewidth=2.0,
        )

        ax_time.plot(
            t_grid,
            pred_re,
            label="Pred Re{h(t)}",
            linewidth=2.0,
        )

        ax_time.plot(
            t_grid,
            target_im,
            label="Target Im{h(t)}",
            linewidth=2.0,
            alpha=0.75,
        )

        ax_time.plot(
            t_grid,
            pred_im,
            label="Pred Im{h(t)}",
            linewidth=2.0,
            alpha=0.75,
        )

        ax_time.set_xlim(T_MIN, T_MAX)
        ax_time.set_ylim(Y_MIN, Y_MAX)

        ax_time.set_xlabel("normalized time")
        ax_time.set_ylabel("channel value")

        ax_time.grid(True, alpha=0.3)
        ax_time.legend(loc="lower right", fontsize=7)

        ax_time.set_title(
            "FAN-style Neural Network\nLearns Multipath Doppler Channel",
            fontsize=17,
            fontweight="bold",
            pad=18,
        )

        info_text = (
            f"Target: h(t)=Σ a·exp(j2πf_Dt+jφ)\n"
            f"Output: [Re{{h(t)}}, Im{{h(t)}}]\n"
            f"Doppler components: {list(DOPPLER_FREQS.astype(int))}\n"
            f"Periodic features: sin(Wt), cos(Wt)\n"
            f"Epoch: {epoch}/{NUM_EPOCHS}\n"
            f"Val Loss: {val_losses[epoch]:.8f}"
        )

        ax_time.text(
            0.03,
            0.96,
            info_text,
            transform=ax_time.transAxes,
            va="top",
            ha="left",
            fontsize=8.0,
            bbox=dict(
                boxstyle="round,pad=0.45",
                facecolor="white",
                alpha=0.88,
            ),
        )

        # ----------------------------
        # IQ trajectory plot
        # ----------------------------
        ax_iq.plot(
            target_re,
            target_im,
            label="Target IQ trajectory",
            linewidth=2.0,
        )

        ax_iq.plot(
            pred_re,
            pred_im,
            label="Pred IQ trajectory",
            linewidth=2.0,
        )

        ax_iq.set_xlim(-1.2, 1.2)
        ax_iq.set_ylim(-1.2, 1.2)
        ax_iq.set_aspect("equal", adjustable="box")

        ax_iq.set_xlabel("Re")
        ax_iq.set_ylabel("Im")

        ax_iq.grid(True, alpha=0.3)
        ax_iq.legend(loc="upper right", fontsize=7)
        ax_iq.set_title("Complex Channel Trajectory", fontsize=11)

        # ----------------------------
        # Loss curve
        # ----------------------------
        epoch_axis = np.arange(len(train_losses))

        ax_loss.plot(
            epoch_axis[: epoch + 1],
            train_losses[: epoch + 1],
            label="Train Loss",
            linewidth=1.6,
        )

        ax_loss.plot(
            epoch_axis[: epoch + 1],
            val_losses[: epoch + 1],
            label="Validation Loss",
            linewidth=1.6,
        )

        ax_loss.scatter(
            [epoch],
            [val_losses[epoch]],
            s=22,
        )

        ax_loss.set_xlim(0, NUM_EPOCHS)

        max_loss_for_plot = max(
            float(np.max(train_losses[:200])),
            float(np.max(val_losses[:200])),
        )

        ax_loss.set_ylim(0, max_loss_for_plot * 1.05)

        ax_loss.set_xlabel("epoch")
        ax_loss.set_ylabel("loss")

        ax_loss.grid(True, alpha=0.3)
        ax_loss.legend(loc="upper right", fontsize=8)

        ax_loss.text(
            0.98,
            0.82,
            f"loss = {val_losses[epoch]:.8f}",
            transform=ax_loss.transAxes,
            va="top",
            ha="right",
            fontsize=8.5,
        )

        writer.grab_frame()

    # Hold final frame for 2 seconds
    final_hold_frames = VIDEO_FPS * 2

    for _ in range(final_hold_frames):
        writer.grab_frame()


plt.close(fig)

print(f"Saved video to: {VIDEO_NAME}")
print("\nDone.")

print("\nOpen with browser:")
print(f"firefox {VIDEO_NAME}")
