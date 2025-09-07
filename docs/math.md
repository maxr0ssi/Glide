# Glide Mathematics Reference

This document summarizes the core math used across Glide for detection, fusion, and scrolling. It mirrors the implementation in `glide/` so you can reason about behavior and tune parameters confidently.

## Coordinate systems and transforms

- Normalized image coordinates: each landmark provides `(x, y) ∈ [0, 1]` (left→right, top→bottom).
- Pixels: `(x_px, y_px) = (x · image_width, y · image_height)`.
- Hand-aligned coordinates (origin at palm center, x-axis along wrist→middle-MCP, scale by index-finger length):
  1) Translate to palm center: `x_rel = x − palm_x`, `y_rel = y − palm_y`.
  2) Rotate by hand angle `θ = atan2(dy, dx)` (wrist→middle MCP):
     - `x_a = cos(−θ)·x_rel − sin(−θ)·y_rel`
     - `y_a = sin(−θ)·x_rel + cos(−θ)·y_rel`
  3) Normalize by finger length `scale` (index tip→index MCP in normalized units):
     - `x_h = x_a / scale`, `y_h = y_a / scale`.

These steps make distances and angles approximately scale-invariant and orientation-invariant across hands and camera positions.

## Distance factor (camera distance proxy)

Let `finger_px = scale · max(image_width, image_height)` be index-finger length in pixels. Map to a distance factor:

`distance_factor = clip((200 − finger_px) / 150, 0, 1)`

- `0.0` = very close (≥200 px finger length), `1.0` = far (≤50 px).

## Proximity metric and scoring

- Normalized proximity distance between fingertips in hand-aligned space:

`d = hypot(x_h_idx − x_h_mid, y_h_idx − y_h_mid)`

- Base piecewise-linear score with thresholds `d_enter < d_exit`:

```
score_prox(d) = 1                         if d ≤ d_enter
                0                         if d ≥ d_exit
                1 − (d − d_enter)/(d_exit − d_enter) otherwise
```

- Distance-aware thresholds (stricter when far): with coefficient `k_d`:

`d_enter'(df) = d_enter · (1 + k_d · df)`

`d_exit'(df)  = d_exit  · (1 + k_d · df)`

Use `score_prox(d)` with `(d_enter', d_exit')`.

- Optional adaptive proximity (when enabled): learn baselines `B_close, B_far` online when not touching. For a given distance factor, interpolate baseline `B(df)` and compute a relative score:

`r = B(df) / (d + 0.001)`

`score_prox_adaptive = 1 / (1 + exp(−s · (r − c)))` with steepness `s` and center `c`.

## Angle metric and scoring

- Fingertip angle from palm center in hand-aligned space: with vectors `v_idx=(x_h_idx, y_h_idx)`, `v_mid=(x_h_mid, y_h_mid)`:

`cos(φ) = (v_idx · v_mid) / (||v_idx|| · ||v_mid||)`

`angle_deg = arccos(cos(φ)) · 180/π`

- Base score with thresholds `θ_enter < θ_exit` (degrees):

```
score_ang(θ) = 1                         if θ ≤ θ_enter
               0                         if θ ≥ θ_exit
               1 − (θ − θ_enter)/(θ_exit − θ_enter) otherwise
```

- Distance-aware thresholds (stricter when close): with coefficient `k_θ` and distance factor `df`:

`θ_enter'(df) = θ_enter − k_θ · (1 − df)`

`θ_exit'(df)  = θ_exit  − k_θ · (1 − df)`

Use `score_ang(θ)` with `(θ_enter', θ_exit')`.

- Angle smoothing: optionally apply EMA with α (e.g., 0.2):

`θ̂_t = α · θ_t + (1 − α) · θ̂_{t−1}`

## Visibility asymmetry score

If MediaPipe visibility `vis_idx, vis_mid` are available:

`a = |vis_idx − vis_mid|`

`score_vis = 1` if `a ≥ a_min`, else `a / a_min`.

## Motion signals

### Velocity correlation (finger kinematics)

Track fingertip positions in hand-aligned space and compute discrete velocities. For sequences `v_idx^x, v_mid^x` and `v_idx^y, v_mid^y` over a window, compute Pearson correlations `ρ_x, ρ_y`; average:

`ρ̄ = (ρ_x + ρ_y) / 2`

`score_corr = 1` if `ρ̄ ≥ ρ_min`, else `max(0, ρ̄)`.

### Micro-Flow Cohesion (MFC, optical flow)

Using Lucas–Kanade at fingertip patches over a short history:

1) Correlation of flow components across history: compute `corr_x, corr_y`, let `corr = (corr_x + corr_y)/2`. NaNs are treated as 0.
2) Magnitude agreement: `mag_ratio = min(⟨||f_idx||⟩, ⟨||f_mid||⟩) / max(⟨||f_idx||⟩, ⟨||f_mid||⟩)`; score 1 if `mag_ratio ∈ [r_min, 1]`, else 0. If both magnitudes ≈ 0, return 0 (conservative).
3) Cohesion:

`score_mfc = 0.7 · max(0, corr) + 0.3 · score_mag_ratio`, clipped to `[0, 1]`.

## Fusion and gating

- Initial fused score (for conditional computation):

`initial_fused = 0.7 · score_prox + 0.3 · score_ang`

- When to compute MFC: when the state machine is READY, or `initial_fused ∈ [0.40, 0.70]`, or when `distance_factor < 0.3` (very close).

- Adaptive fusion weights by distance factor:

Near (`df < 0.3`): `w = {prox: 0.40, ang: 0.30, mfc: 0.25, occ: 0.05}`

Far (`df > 0.7`): `w = {prox: 0.45, ang: 0.20, mfc: 0.30, occ: 0.05}`

Medium: linear interpolation with `t = (df − 0.3)/0.4`:

`w(df) = (1 − t)·w_near + t·w_far`

- Final fused score:

`fused = w_prox · score_prox' + w_ang · score_ang' + w_mfc · score_mfc + w_occ · score_vis`

(`score_prox'`, `score_ang'` are the distance-aware or adaptive versions.)

## State machine and hysteresis

Two states: `UNARMED` (not touching) and `READY` (touching). Let `T_enter`, `T_exit` be fused thresholds, and `N_enter`, `N_exit` be required consecutive frames.

- UNARMED → READY: increment a counter while `fused > T_enter`; transition when it reaches `N_enter`.
- READY → UNARMED: increment a counter while `fused < T_exit`; transition when it reaches `N_exit`.

This prevents flicker and establishes hysteresis.

## Smoothing (EMA)

- Proximity score smoothing (if enabled): `p̂_t = α · p_t + (1 − α) · p̂_{t−1}`.
- Angle smoothing: `θ̂_t = α · θ_t + (1 − α) · θ̂_{t−1}` (α ≈ 0.2).

## Velocity tracking and scrolling

### Velocity tracking

Track midpoint of index and middle fingertips `(x_m, y_m)` in normalized units.

Over a window `[t₀, t₁]` (≈100 ms):

`v_x = (x_m(t₁) − x_m(t₀)) · 1000 / (t₁ − t₀)`

`v_y = (y_m(t₁) − y_m(t₀)) · 1000 / (t₁ − t₀)`

Apply component-wise EMA with smoothing factor `β` (≈0.3) and a small noise threshold to zero out jitter. Velocity is in normalized units per second.

### Scroll mapping (macOS continuous scroll)

Map normalized velocity to pixel deltas each frame with scale `S` (≈500):

`Δx_px = S · v_x`, `Δy_px = S · v_y` (invert `Δy_px` if macOS natural scrolling is enabled).

Clamp each axis to `± max_velocity`. Generate CGEvent scrolls with proper phases: Began → Changed → Ended; momentum is handled by macOS.

## Parameters (key symbols)

- Proximity thresholds: `d_enter, d_exit`, hard cap `d_hard`.
- Angle thresholds: `θ_enter, θ_exit`, hard cap `θ_hard` (degrees).
- Distance interaction: `k_d, k_θ`.
- Fusion thresholds and frames: `T_enter, T_exit, N_enter, N_exit`.
- Correlation minimums: `ρ_min` (kinematics), flow magnitude ratio band `[r_min, 1]`.
- EMA factors: `α` (proximity), `α_angle`.
- Adaptive proximity: baseline learning rate `λ`, center `c`, steepness `s`.
- Velocity tracker: window `W_ms`, smoothing `β`, noise threshold.
- Scroll mapping: scale `S`, clamp `max_velocity`.

All configurable in `glide/io/defaults.yaml` (validated by `glide/core/config_models.py`).
