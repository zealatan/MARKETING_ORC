# temp_fan_sine.py
#
# FAN-style neural network learns a high-frequency sine wave.
#
# Target:
#   y = sin(20x)
#
# Output:
#   training_video_out_fan/
#     ├── fan_sine_training_trace.npz
#     └── fan_sine_training_dynamic.mp4
#
# Run:
#   python3 temp_fan_sine.py
#
# Open:
#   firefox training_video_out_fan/fan_sine_training_dynamic.mp4

import os
import numpy as np
import torch
import torch.nn as nn
import matplotlib.pyplot as plt
from matplotlib.animation import FFMpegWriter


# ============================================================
# 1. Config
# ============================================================

OUT_DIR = "training_video_out_fan"
os.makedirs(OUT_DIR, exist_ok=True)

SEED = 0

NUM_EPOCHS = 4000
SAVE_EVERY = 10

LR = 5e-4

N_TRAIN = 1024
N_VAL = 1024
N_GRID = 2000

VIDEO_FPS = 30

VIDEO_NAME = os.path.join(OUT_DIR, "fan_sine_training_dynamic.mp4")
NPZ_NAME = os.path.join(OUT_DIR, "fan_sine_training_trace.npz")

DEVICE = "cuda" if torch.cuda.is_available() else "cpu"

# High-frequency sine setting
FREQ = 20.0

X_MIN = -2.0 * np.pi
X_MAX =  2.0 * np.pi

Y_MIN = -1.5
Y_MAX =  1.5


# ============================================================
# 2. Reproducibility
# ============================================================

torch.manual_seed(SEED)
np.random.seed(SEED)

if DEVICE == "cuda":
    torch.cuda.manual_seed_all(SEED)


# ============================================================
# 3. Target function
# ============================================================

def target_function_np(x: np.ndarray) -> np.ndarray:
    """
    x: shape [N]
    y: shape [N]
    """
    y = np.sin(FREQ * x)
    return y.astype(np.float32)


# ============================================================
# 4. Dataset
# ============================================================

x_train = np.random.uniform(X_MIN, X_MAX, size=(N_TRAIN, 1)).astype(np.float32)
y_train = target_function_np(x_train[:, 0]).reshape(-1, 1)

x_val = np.random.uniform(X_MIN, X_MAX, size=(N_VAL, 1)).astype(np.float32)
y_val = target_function_np(x_val[:, 0]).reshape(-1, 1)

x_grid = np.linspace(X_MIN, X_MAX, N_GRID).astype(np.float32)
y_grid = target_function_np(x_grid)

x_train_t = torch.tensor(x_train, device=DEVICE)
y_train_t = torch.tensor(y_train, device=DEVICE)

x_val_t = torch.tensor(x_val, device=DEVICE)
y_val_t = torch.tensor(y_val, device=DEVICE)

x_grid_t = torch.tensor(x_grid.reshape(-1, 1), device=DEVICE)


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

    This is not an official paper implementation.
    It is a compact educational implementation for visual experiments.
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

            nn.Linear(128, 1),
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
print(f"Target function: y = sin({FREQ}x)")
print("Start training...\n")

for epoch in range(NUM_EPOCHS + 1):

    # ----------------------------
    # Training step
    # ----------------------------
    model.train()

    optimizer.zero_grad()

    pred_train = model(x_train_t)
    loss = criterion(pred_train, y_train_t)

    loss.backward()
    optimizer.step()

    # ----------------------------
    # Evaluate updated model
    # ----------------------------
    model.eval()

    with torch.no_grad():
        train_loss_eval = criterion(model(x_train_t), y_train_t)
        val_loss_eval = criterion(model(x_val_t), y_val_t)

    train_losses.append(float(train_loss_eval.item()))
    val_losses.append(float(val_loss_eval.item()))

    # ----------------------------
    # Save prediction for video
    # ----------------------------
    if epoch % SAVE_EVERY == 0:
        with torch.no_grad():
            pred_grid = model(x_grid_t).detach().cpu().numpy().reshape(-1)

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
    x_grid=x_grid,
    y_grid=y_grid,
    saved_epochs=saved_epochs,
    pred_history=pred_history,
    train_losses=train_losses,
    val_losses=val_losses,
    num_epochs=NUM_EPOCHS,
    save_every=SAVE_EVERY,
    freq=FREQ,
    x_min=X_MIN,
    x_max=X_MAX,
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

ax_main = fig.add_axes([0.12, 0.34, 0.82, 0.55])
ax_loss = fig.add_axes([0.12, 0.12, 0.82, 0.15])

metadata = dict(title="FAN-style Neural Network Learns High-Frequency Sine")
writer = FFMpegWriter(fps=VIDEO_FPS, metadata=metadata)

with writer.saving(fig, VIDEO_NAME, dpi=180):

    for i, epoch in enumerate(saved_epochs):

        ax_main.clear()
        ax_loss.clear()

        pred_y = pred_history[i]

        # ----------------------------
        # Main prediction plot
        # ----------------------------
        ax_main.plot(
            x_grid,
            y_grid,
            label=f"Target: sin({int(FREQ)}x)",
            linewidth=2.2,
        )

        ax_main.plot(
            x_grid,
            pred_y,
            label="FAN-style NN",
            linewidth=2.2,
        )

        ax_main.set_xlim(X_MIN, X_MAX)
        ax_main.set_ylim(Y_MIN, Y_MAX)

        ax_main.set_xlabel("x")
        ax_main.set_ylabel("y")

        ax_main.grid(True, alpha=0.3)
        ax_main.legend(loc="lower right")

        ax_main.set_title(
            "FAN-style Neural Network\nLearns High-Frequency Sine",
            fontsize=18,
            fontweight="bold",
            pad=20,
        )

        info_text = (
            f"Model: FAN-style MLP\n"
            f"Periodic features: sin(Wx), cos(Wx)\n"
            f"Target: sin({int(FREQ)}x)\n"
            f"Loss: MSE\n"
            f"Epoch: {epoch}/{NUM_EPOCHS}\n"
            f"Val Loss: {val_losses[epoch]:.8f}"
        )

        ax_main.text(
            0.03,
            0.96,
            info_text,
            transform=ax_main.transAxes,
            va="top",
            ha="left",
            fontsize=9,
            bbox=dict(
                boxstyle="round,pad=0.45",
                facecolor="white",
                alpha=0.88,
            ),
        )

        # ----------------------------
        # Loss curve
        # ----------------------------
        epoch_axis = np.arange(len(train_losses))

        ax_loss.plot(
            epoch_axis[: epoch + 1],
            train_losses[: epoch + 1],
            label="Train Loss",
            linewidth=1.8,
        )

        ax_loss.plot(
            epoch_axis[: epoch + 1],
            val_losses[: epoch + 1],
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
            fontsize=9,
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
