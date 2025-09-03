# MacBook Pro Camera Optimization

## Problem
MacBook Pro's downward-tilted camera causes:
- Vertical foreshortening that inflates finger convergence angles
- Increased angle jitter from perspective distortion
- Higher uncertainty when hands are close to the camera

## Quick Wins Implemented

### 1. Configuration Adjustments (`defaults.yaml`)
- **Relaxed angle thresholds**:
  - `angle_enter_deg`: 20.0 → 24.0 (+20% tolerance)
  - `angle_exit_deg`: 28.0 → 32.0 (+14% tolerance)
  - `k_theta`: 4.0 → 2.0 (reduced "stricter when close" effect)
- **Improved stability**:
  - `frames_to_enter`: 3 → 4 (reduce false positives from angle flicker)
  - `fused_enter_threshold`: 0.80 → 0.75 (easier to trigger)
  - `fused_exit_threshold`: 0.60 → 0.58 (maintains hysteresis width)

### 2. Adaptive Weight Rebalancing
When close to camera (distance_factor < 0.3):
- **Before**: proximity 50%, angle 35%, mfc 10%, occlusion 5%
- **After**: proximity 55%, angle 25%, mfc 15%, occlusion 5%
- Reduces reliance on angle which is most affected by camera tilt

### 3. Expanded MFC Computation
- **Before**: Only computed when 0.45 ≤ initial_fused ≤ 0.65
- **After**: 
  - Expanded band: 0.40 ≤ initial_fused ≤ 0.70
  - Always compute when very close (distance_factor < 0.3)
- Provides more optical flow data when angle is unreliable

### 4. Angle Smoothing
- Added EMA smoothing to angle_score (α = 0.2)
- Reduces jitter from perspective-induced angle variations
- Faster response than proximity smoothing (0.2 vs 0.3)

## Results
These changes make TouchProof more reliable on MacBook Pro cameras by:
- Compensating for systematic angle inflation from camera tilt
- Reducing sensitivity to angle-based noise when close
- Leveraging optical flow (MFC) more often as a stabilizing signal
- Smoothing out perspective-induced jitter

## Future Improvements
Consider adding:
- Y-axis foreshortening compensation in HandAligner
- Camera profile detection (laptop vs external webcam)
- Automatic calibration for different camera angles