import os
import numpy as np
import torch
import torch.nn as nn
import matplotlib.pyplot as plt
from matplotlib.animation import FFMpegWriter


# ============================================================
# 1. Config
# ============================================================

OUT_DIR = "training_video_out_fan_denoise"
os.makedirs(OUT_DIR, exist_ok=True)

SEED = 0

NUM_EPOCHS = 4000
SAVE_EVERY = 10

LR = 5e-4
WEIGHT_DECAY = 1e-4

N_TRAIN = 4096
N_VAL = 2048
N_GRID = 2000

VIDEO_FPS = 30

VIDEO_NAME = os.path.join(OUT_DIR, "fan_doppler_denoise_dynamic.mp4")
NPZ_NAME = os.path.join(OUT_DIR, "fan_doppler_denoise_trace.npz")

DEVICE = "cuda" if torch.cuda.is_available() else "cpu"

PILOT_SNR_DB = 8.0

# "noisy" = realistic mode. Train only from noisy pilot observations.
# "clean" = oracle supervised mode. Train directly with clean channel.
TRAIN_TARGET_MODE = "noisy"

T_MIN = 0.0
T_MAX = 1.0

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

DOPPLER_FREQS = np.array([3.0, 7.0, 13.0, 21.0], dtype=np.float32)
PATH_AMPS = np.array([1.0, 0.55, 0.35, 0.22], dtype=np.float32)
PATH_PHASES = np.array([0.2, 1.7, -0.9, 2.4], dtype=np.float32)


def target_channel_np(t: np.ndarray) -> np.ndarray:
    h = np.zeros_like(t, dtype=np.complex64)

    for amp, fd, phase in zip(PATH_AMPS, DOPPLER_FREQS, PATH_PHASES):
        h += amp * np.exp(1j * (2.0 * np.pi * fd * t + phase))

    h = h / np.sum(PATH_AMPS)

    y = np.stack(
        [
            np.real(h),
            np.imag(h),
        ],
        axis=-1,
    ).astype(np.float32)

    return y


def add_complex_awgn_np(
    y_clean: np.ndarray,
    snr_db: float,
    rng: np.random.Generator,
) -> np.ndarray:
    h = y_clean[:, 0] + 1j * y_clean[:, 1]

    signal_power = np.mean(np.abs(h) ** 2)
    snr_linear = 10.0 ** (snr_db / 10.0)

    noise_power = signal_power / snr_linear
    noise_std_per_dim = np.sqrt(noise_power / 2.0)

    noise = noise_std_per_dim * (
        rng.standard_normal(h.shape).astype(np.float32)
        + 1j * rng.standard_normal(h.shape).astype(np.float32)
    )

    h_noisy = h + noise

    y_noisy = np.stack(
        [
            np.real(h_noisy),
            np.imag(h_noisy),
        ],
        axis=-1,
    ).astype(np.float32)

    return y_noisy


def complex_mse_np(y_pred: np.ndarray, y_ref: np.ndarray) -> float:
    diff_re = y_pred[:, 0] - y_ref[:, 0]
    diff_im = y_pred[:, 1] - y_ref[:, 1]
    return float(np.mean(diff_re * diff_re + diff_im * diff_im))


def phase_error_rad_np(y_pred: np.ndarray, y_ref: np.ndarray) -> float:
    h_pred = y_pred[:, 0] + 1j * y_pred[:, 1]
    h_ref = y_ref[:, 0] + 1j * y_ref[:, 1]

    eps = 1e-8
    valid = (np.abs(h_pred) > eps) & (np.abs(h_ref) > eps)

    if not np.any(valid):
        return float("nan")

    phase_err = np.angle(h_pred[valid] * np.conj(h_ref[valid]))
    return float(np.mean(np.abs(phase_err)))


# ============================================================
# 4. Dataset
# ============================================================

rng_train = np.random.default_rng(SEED + 100)
rng_val = np.random.default_rng(SEED + 200)
rng_grid = np.random.default_rng(SEED + 300)

t_train = np.random.uniform(T_MIN, T_MAX, size=(N_TRAIN, 1)).astype(np.float32)
y_train_clean = target_channel_np(t_train[:, 0])
y_train_noisy = add_complex_awgn_np(y_train_clean, PILOT_SNR_DB, rng_train)

t_val = np.random.uniform(T_MIN, T_MAX, size=(N_VAL, 1)).astype(np.float32)
y_val_clean = target_channel_np(t_val[:, 0])
y_val_noisy = add_complex_awgn_np(y_val_clean, PILOT_SNR_DB, rng_val)

t_grid = np.linspace(T_MIN, T_MAX, N_GRID).astype(np.float32)
y_grid_clean = target_channel_np(t_grid)
y_grid_noisy = add_complex_awgn_np(y_grid_clean, PILOT_SNR_DB, rng_grid)

if TRAIN_TARGET_MODE == "noisy":
    y_train_target = y_train_noisy
    y_val_target = y_val_noisy
elif TRAIN_TARGET_MODE == "clean":
    y_train_target = y_train_clean
    y_val_target = y_val_clean
else:
    raise ValueError("TRAIN_TARGET_MODE must be either 'noisy' or 'clean'.")

t_train_t = torch.tensor(t_train, device=DEVICE)
y_train_target_t = torch.tensor(y_train_target, device=DEVICE)
y_train_clean_t = torch.tensor(y_train_clean, device=DEVICE)

t_val_t = torch.tensor(t_val, device=DEVICE)
y_val_target_t = torch.tensor(y_val_target, device=DEVICE)
y_val_clean_t = torch.tensor(y_val_clean, device=DEVICE)

t_grid_t = torch.tensor(t_grid.reshape(-1, 1), device=DEVICE)


# ============================================================
# 5. FAN-style Layer
# ============================================================

class FANLayer(nn.Module):
    def __init__(
        self,
        in_dim: int,
        out_dim: int,
        periodic_dim: int = 48,
        nonperiodic_dim: int = 48,
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

        return self.output_linear(features)


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
                periodic_dim=48,
                nonperiodic_dim=48,
            ),
            nn.ReLU(),

            FANLayer(
                in_dim=128,
                out_dim=128,
                periodic_dim=48,
                nonperiodic_dim=48,
            ),
            nn.ReLU(),

            nn.Linear(128, 2),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.net(x)


model = FANNet().to(DEVICE)

optimizer = torch.optim.AdamW(
    model.parameters(),
    lr=LR,
    weight_decay=WEIGHT_DECAY,
)

criterion = nn.MSELoss()


# ============================================================
# 7. Training + history saving
# ============================================================

train_losses = []
val_losses = []
val_clean_mse_losses = []

saved_epochs = []
pred_history = []

grid_clean_mse_history = []
grid_phase_error_history = []

print(f"Using device: {DEVICE}")
print("Step 2: Noisy pilot observation -> clean Doppler channel denoising")
print(f"Pilot SNR: {PILOT_SNR_DB:.1f} dB")
print(f"Training target mode: {TRAIN_TARGET_MODE}")
print("Model output: [Re{h(t)}, Im{h(t)}]")
print("Start training...\n")

for epoch in range(NUM_EPOCHS + 1):

    model.train()

    optimizer.zero_grad()

    pred_train = model(t_train_t)
    loss = criterion(pred_train, y_train_target_t)

    loss.backward()
    optimizer.step()

    model.eval()

    with torch.no_grad():
        pred_train_eval = model(t_train_t)
        pred_val_eval = model(t_val_t)

        train_loss_eval = criterion(pred_train_eval, y_train_target_t)
        val_loss_eval = criterion(pred_val_eval, y_val_target_t)

        val_clean_mse_eval = criterion(pred_val_eval, y_val_clean_t)

    train_losses.append(float(train_loss_eval.item()))
    val_losses.append(float(val_loss_eval.item()))
    val_clean_mse_losses.append(float(val_clean_mse_eval.item()))

    if epoch % SAVE_EVERY == 0:
        with torch.no_grad():
            pred_grid = model(t_grid_t).detach().cpu().numpy()

        clean_mse_grid = complex_mse_np(pred_grid, y_grid_clean)
        phase_err_grid = phase_error_rad_np(pred_grid, y_grid_clean)

        saved_epochs.append(epoch)
        pred_history.append(pred_grid.astype(np.float32))
        grid_clean_mse_history.append(clean_mse_grid)
        grid_phase_error_history.append(phase_err_grid)

    if epoch % 100 == 0:
        print(
            f"Epoch {epoch:5d}/{NUM_EPOCHS} | "
            f"Train Target Loss: {train_losses[-1]:.8f} | "
            f"Val Target Loss: {val_losses[-1]:.8f} | "
            f"Hidden Clean MSE: {val_clean_mse_losses[-1]:.8f}"
        )


saved_epochs = np.array(saved_epochs, dtype=np.int32)
pred_history = np.stack(pred_history, axis=0)

train_losses = np.array(train_losses, dtype=np.float32)
val_losses = np.array(val_losses, dtype=np.float32)
val_clean_mse_losses = np.array(val_clean_mse_losses, dtype=np.float32)

grid_clean_mse_history = np.array(grid_clean_mse_history, dtype=np.float32)
grid_phase_error_history = np.array(grid_phase_error_history, dtype=np.float32)

np.savez(
    NPZ_NAME,
    t_grid=t_grid,
    y_grid_clean=y_grid_clean,
    y_grid_noisy=y_grid_noisy,
    saved_epochs=saved_epochs,
    pred_history=pred_history,
    train_losses=train_losses,
    val_losses=val_losses,
    val_clean_mse_losses=val_clean_mse_losses,
    grid_clean_mse_history=grid_clean_mse_history,
    grid_phase_error_history=grid_phase_error_history,
    num_epochs=NUM_EPOCHS,
    save_every=SAVE_EVERY,
    pilot_snr_db=PILOT_SNR_DB,
    train_target_mode=TRAIN_TARGET_MODE,
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

fig = plt.figure(figsize=(6, 10.67))

ax_time = fig.add_axes([0.12, 0.56, 0.82, 0.33])
ax_iq = fig.add_axes([0.18, 0.31, 0.70, 0.18])
ax_loss = fig.add_axes([0.12, 0.10, 0.82, 0.13])

metadata = dict(title="FAN-style NN Denoises Multipath Doppler Channel")
writer = FFMpegWriter(fps=VIDEO_FPS, metadata=metadata)

scatter_step = max(1, N_GRID // 300)
scatter_idx = np.arange(0, N_GRID, scatter_step)

with writer.saving(fig, VIDEO_NAME, dpi=180):

    for i, epoch in enumerate(saved_epochs):

        ax_time.clear()
        ax_iq.clear()
        ax_loss.clear()

        pred_y = pred_history[i]

        clean_re = y_grid_clean[:, 0]
        clean_im = y_grid_clean[:, 1]

        noisy_re = y_grid_noisy[:, 0]
        noisy_im = y_grid_noisy[:, 1]

        pred_re = pred_y[:, 0]
        pred_im = pred_y[:, 1]

        ax_time.plot(
            t_grid,
            clean_re,
            label="Clean Re{h(t)}",
            linewidth=2.0,
        )

        ax_time.plot(
            t_grid,
            pred_re,
            label="FAN Denoised Re{h(t)}",
            linewidth=2.0,
        )

        ax_time.scatter(
            t_grid[scatter_idx],
            noisy_re[scatter_idx],
            label="Noisy Pilot Re",
            s=7,
            alpha=0.28,
        )

        ax_time.plot(
            t_grid,
            clean_im,
            label="Clean Im{h(t)}",
            linewidth=2.0,
            alpha=0.70,
        )

        ax_time.plot(
            t_grid,
            pred_im,
            label="FAN Denoised Im{h(t)}",
            linewidth=2.0,
            alpha=0.70,
        )

        ax_time.scatter(
            t_grid[scatter_idx],
            noisy_im[scatter_idx],
            label="Noisy Pilot Im",
            s=7,
            alpha=0.20,
        )

        ax_time.set_xlim(T_MIN, T_MAX)
        ax_time.set_ylim(Y_MIN, Y_MAX)

        ax_time.set_xlabel("normalized time")
        ax_time.set_ylabel("channel value")

        ax_time.grid(True, alpha=0.3)
        ax_time.legend(loc="lower right", fontsize=6.5)

        ax_time.set_title(
            "FAN-style Neural Network\nDenoises Doppler Channel Pilots",
            fontsize=17,
            fontweight="bold",
            pad=18,
        )

        info_text = (
            f"Clean: h(t)=sum a exp(j2pi f_D t + j phi)\n"
            f"Observation: noisy pilot h_p(t)=h(t)+w\n"
            f"Pilot SNR: {PILOT_SNR_DB:.1f} dB\n"
            f"Training target: {TRAIN_TARGET_MODE} pilot trajectory\n"
            f"Periodic features: sin(Wt), cos(Wt)\n"
            f"Epoch: {epoch}/{NUM_EPOCHS}\n"
            f"Clean MSE: {grid_clean_mse_history[i]:.8f}\n"
            f"Phase Err: {grid_phase_error_history[i]:.5f} rad"
        )

        ax_time.text(
            0.03,
            0.96,
            info_text,
            transform=ax_time.transAxes,
            va="top",
            ha="left",
            fontsize=7.6,
            bbox=dict(
                boxstyle="round,pad=0.45",
                facecolor="white",
                alpha=0.88,
            ),
        )

        ax_iq.plot(
            clean_re,
            clean_im,
            label="Clean IQ trajectory",
            linewidth=2.0,
        )

        ax_iq.scatter(
            noisy_re[scatter_idx],
            noisy_im[scatter_idx],
            label="Noisy pilots",
            s=8,
            alpha=0.25,
        )

        ax_iq.plot(
            pred_re,
            pred_im,
            label="FAN denoised trajectory",
            linewidth=2.0,
        )

        ax_iq.set_xlim(-1.2, 1.2)
        ax_iq.set_ylim(-1.2, 1.2)
        ax_iq.set_aspect("equal", adjustable="box")

        ax_iq.set_xlabel("Re")
        ax_iq.set_ylabel("Im")

        ax_iq.grid(True, alpha=0.3)
        ax_iq.legend(loc="upper right", fontsize=6.5)
        ax_iq.set_title("Complex Channel Trajectory", fontsize=11)

        epoch_axis = np.arange(len(train_losses))

        ax_loss.plot(
            epoch_axis[: epoch + 1],
            train_losses[: epoch + 1],
            label="Train target loss",
            linewidth=1.5,
        )

        ax_loss.plot(
            epoch_axis[: epoch + 1],
            val_losses[: epoch + 1],
            label="Val target loss",
            linewidth=1.5,
        )

        ax_loss.plot(
            epoch_axis[: epoch + 1],
            val_clean_mse_losses[: epoch + 1],
            label="Hidden clean MSE",
            linewidth=1.7,
        )

        ax_loss.scatter(
            [epoch],
            [val_clean_mse_losses[epoch]],
            s=22,
        )

        ax_loss.set_xlim(0, NUM_EPOCHS)

        max_loss_for_plot = max(
            float(np.max(train_losses[:200])),
            float(np.max(val_losses[:200])),
            float(np.max(val_clean_mse_losses[:200])),
        )

        ax_loss.set_ylim(0, max_loss_for_plot * 1.05)

        ax_loss.set_xlabel("epoch")
        ax_loss.set_ylabel("loss / MSE")

        ax_loss.grid(True, alpha=0.3)
        ax_loss.legend(loc="upper right", fontsize=6.8)

        ax_loss.text(
            0.98,
            0.82,
            f"clean MSE = {val_clean_mse_losses[epoch]:.8f}",
            transform=ax_loss.transAxes,
            va="top",
            ha="right",
            fontsize=8.2,
        )

        writer.grab_frame()

    final_hold_frames = VIDEO_FPS * 2

    for _ in range(final_hold_frames):
        writer.grab_frame()


plt.close(fig)

print(f"Saved video to: {VIDEO_NAME}")
print("\nDone.")

print("\nOpen with browser:")
print(f"firefox {VIDEO_NAME}")

