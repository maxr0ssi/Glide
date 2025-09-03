# Proximity Detection Improvements

## Problem Solved
The fixed proximity thresholds (0.25 enter, 0.40 exit) didn't work well at different distances from the camera. The system was making it HARDER to detect touch when far away, which is the opposite of what's needed.

## Improvements Implemented

### 1. Fixed Distance Adjustment Logic
**Before**: Made thresholds stricter when far (wrong direction)
```python
enter_adjusted = proximity_enter * (1 + k_d * distance_factor)  # WRONG
```
**After**: Made thresholds more lenient when far
```python
enter_adjusted = proximity_enter * (1 + k_d * (1 - distance_factor))  # CORRECT
```

### 2. Adaptive Baseline Learning
- Tracks "typical" finger separation at different distances
- Learns separate baselines for close (< 0.3) and far (> 0.7) distances
- Detects touch based on relative change from baseline
- Touch triggered when fingers are at 85% of typical distance

### 3. Logarithmic Distance Option
- Added `get_normalized_distance_log()` method
- Uses log scaling: `log(1 + distance) / log(1 + reference)`
- More stable across different camera distances
- Compresses large distances, expands small ones

### 4. Configurable Proximity Modes
New config options in `defaults.yaml`:
```yaml
proximity_mode: "adaptive"   # "fixed", "adaptive", or "logarithmic"
baseline_learning_rate: 0.02 # How fast to learn baseline distances
relative_touch_threshold: 0.85 # Touch when at 85% of baseline
```

## How It Works

### Fixed Mode (default fallback)
- Uses configured thresholds with distance-based adjustment
- Thresholds become more lenient when hand is far from camera

### Adaptive Mode (recommended)
- Learns what "normal" finger separation looks like at different distances
- Detects touch based on relative change from normal
- Self-calibrates to different users and camera setups

### Logarithmic Mode
- Uses log-normalized distances instead of linear
- Better stability across distance ranges
- Good for environments with varying camera distances

## Benefits
1. **Consistent detection** across all distances from camera
2. **Self-calibrating** to different users and setups
3. **More reliable** on MacBook Pro cameras
4. **Configurable** for different use cases

## Usage
The system defaults to adaptive mode. To change:
```yaml
touchproof:
  proximity_mode: "logarithmic"  # or "fixed" or "adaptive"
```