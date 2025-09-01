# TouchProof Scoring System Improvements

## Executive Summary

This document outlines improvements to the TouchProof fingertip detection system based on analysis of the current implementation. The improvements focus on making the system more adaptive to varying conditions while maintaining its core architecture.

## Current System Analysis

### What's Working Well
- **Multi-signal fusion architecture**: Combining proximity, angle, MFC, and visibility signals
- **Distance-aware adaptation**: Using distance_factor to modulate thresholds and weights (not as direct evidence)
- **Hard caps for early rejection**: Efficient filtering of obviously non-touching states
- **Hysteresis state machine**: Temporal stability through frame counting

### Identified Issues
1. **Linear scoring functions** assume uniform information density across ranges, but fingertip perception and noise don't scale linearly
2. **Fixed adaptation coefficients** (k_d=0.3, k_theta=4.0) don't account for camera/lens/user variation
3. **MFC gating creates blind spots** by withholding motion coherence computation in edge cases where it might be most needed
4. **No noise adaptation** - thresholds remain static regardless of tracking quality or environmental conditions
5. **Weak confidence handling** - visibility/occlusion signals have minimal impact even when landmarks are poor

## Improvement Plan

### Phase 1: High-Impact Changes (Priority)

#### 1. Logistic Proximity Scoring
Replace linear interpolation with adaptive logistic function:

```python
def _score_proximity_logistic(self, distance_norm: float, distance_factor: float) -> float:
    """Score proximity using logistic curve with distance-adaptive parameters."""
    # Center shifts with distance
    mu = self.config.proximity_enter + 0.5 * (self.config.proximity_exit - self.config.proximity_enter) * distance_factor
    # Scale increases with distance (wider uncertainty band when far)
    sigma = 0.15 * (self.config.proximity_exit - self.config.proximity_enter) * (1 + 0.5 * distance_factor)
    return 1.0 / (1.0 + math.exp((distance_norm - mu) / sigma))
```

**Benefits**: Smoother transitions, better matches human perception, naturally handles noise at boundaries

#### 2. Noise-Adaptive Thresholds
Add calibration phase to measure idle hand jitter:

```python
def calibrate_noise(self, landmarks: List[Landmark], frame_count: int):
    """Measure idle noise during first 60 frames (~2 seconds)."""
    if frame_count < self.config.noise_calibration_frames:
        # Track fingertip movement when idle
        self._noise_measurements.append(compute_tip_delta(landmarks))
    elif frame_count == self.config.noise_calibration_frames:
        # Compute noise level as 95th percentile of movements
        self._idle_noise_level = np.percentile(self._noise_measurements, 95)
```

Then apply to thresholds:
```python
# In scoring functions
noise_factor = 1 + self.config.noise_scale_factor * min(self._idle_noise_level, 0.3)
enter_adjusted = self.config.proximity_enter * noise_factor
```

**Benefits**: Automatic adaptation to camera quality, lighting, and hand steadiness

#### 3. Expanded MFC Computation Triggers
Current: Only when `state == READY or initial_fused ∈ [0.45, 0.65]`

New conditions:
```python
compute_mfc = (
    self.state == GateState.READY or
    (0.45 <= initial_fused <= 0.65) or
    abs(proximity_score - 0.5) < 0.15 or  # Near decision boundary
    abs(angle_score - 0.5) < 0.15 or      # Near decision boundary  
    avg_visibility < 0.8                   # Low confidence in landmarks
)
```

**Benefits**: MFC available when most needed for disambiguation

#### 4. Dynamic Distance Coefficients
Replace fixed k_d and k_theta:

```python
def _k_d(self, distance_factor: float) -> float:
    """Proximity distance coefficient - increases with distance."""
    # Quadratic for smooth progression
    return 0.2 + 0.3 * distance_factor + 0.2 * distance_factor**2

def _k_theta(self, distance_factor: float) -> float:
    """Angle distance coefficient - decreases with distance."""
    # Higher when close (stricter angle requirements)
    return 6.0 * (1 - distance_factor) + 1.0
```

**Benefits**: Better matches actual perception changes across distances

#### 5. Confidence-Weighted Fusion
Track landmark quality and adjust weights:

```python
def _get_confidence_adjusted_weights(self, base_weights: Dict, avg_visibility: float) -> Dict:
    """Adjust weights based on tracking confidence."""
    if avg_visibility < self.config.visibility_low_threshold:
        confidence_scale = avg_visibility / self.config.visibility_low_threshold
        # Reduce reliance on position-based signals
        adjusted = base_weights.copy()
        adjusted['proximity'] *= (0.7 + 0.3 * confidence_scale)
        adjusted['angle'] *= (0.7 + 0.3 * confidence_scale)
        # Increase reliance on motion
        mfc_boost = (1 - confidence_scale) * 0.2
        adjusted['mfc'] += mfc_boost
        # Renormalize
        total = sum(adjusted.values())
        return {k: v/total for k, v in adjusted.items()}
    return base_weights
```

**Benefits**: Graceful degradation when tracking quality drops

### Phase 2: Medium-Term Improvements

#### 6. Temporal Smoothing with Derivative Constraints
Replace simple frame counting with EMA + derivative checking:

```python
def _update_state_smooth(self, fused_score: float) -> bool:
    """State machine with smoothed score and derivative constraints."""
    # Update EMA
    if self._fused_ema is None:
        self._fused_ema = fused_score
        self._fused_derivative = 0.0
    else:
        alpha = self.config.fused_ema_alpha
        new_ema = alpha * fused_score + (1 - alpha) * self._fused_ema
        self._fused_derivative = new_ema - self._fused_ema
        self._fused_ema = new_ema
    
    # State transitions on smoothed score
    if self.state == GateState.UNARMED:
        if self._fused_ema > self.config.fused_enter_threshold and self._fused_derivative > 0:
            # Require positive trend
            return self._confirm_state_change(True)
    elif self.state == GateState.READY:
        if self._fused_ema < self.config.fused_exit_threshold and self._fused_derivative < 0:
            # Require negative trend
            return self._confirm_state_change(False)
    
    return self.state == GateState.READY
```

**Benefits**: Smoother transitions, rejects noise spikes

#### 7. Lightweight Merge Confidence Signal
Add simple gradient-based visual check:

```python
def _compute_merge_confidence(self, frame_gray: np.ndarray, tip_a: Tuple, tip_b: Tuple, 
                            distance_factor: float) -> float:
    """Lightweight visual merge detection using gradient magnitude."""
    # Adaptive strip width
    strip_width = int(4 + 6 * distance_factor)
    
    # Sample points along line between tips
    n_samples = 20
    points = np.linspace(tip_a, tip_b, n_samples)
    
    # Compute gradient magnitude at each point
    gradients = []
    for pt in points[1:-1]:  # Skip endpoints
        x, y = int(pt[0]), int(pt[1])
        if 0 <= x < frame_gray.shape[1] and 0 <= y < frame_gray.shape[0]:
            # Simple Sobel gradient
            gx = cv2.Sobel(frame_gray[y-1:y+2, x-1:x+2], cv2.CV_32F, 1, 0, ksize=3)
            gy = cv2.Sobel(frame_gray[y-1:y+2, x-1:x+2], cv2.CV_32F, 0, 1, ksize=3)
            grad_mag = np.sqrt(gx**2 + gy**2).mean()
            gradients.append(grad_mag)
    
    # Low gradient = likely merged
    if gradients:
        avg_gradient = np.mean(gradients)
        # Normalize to [0, 1] where 1 = merged (low gradient)
        return 1.0 - min(avg_gradient / 50.0, 1.0)
    return 0.5  # Uncertain
```

**Benefits**: Additional visual evidence with minimal computational cost

### Configuration Updates

Add these parameters to `TouchProofConfig`:

```python
# Noise adaptation
noise_calibration_frames: int = 60      # ~2 seconds at 30fps
noise_scale_factor: float = 1.2         # How much noise affects thresholds

# Confidence handling  
visibility_low_threshold: float = 0.8    # Below this, adjust weights
confidence_weight_scale: float = 0.7     # Min scale for position signals

# MFC computation
mfc_uncertainty_band: float = 0.15       # Expand MFC computation zone

# Temporal smoothing
fused_ema_alpha: float = 0.4            # EMA smoothing factor
derivative_threshold: float = 0.01       # Min derivative for state change

# Merge confidence (Phase 2)
enable_merge_confidence: bool = False    # Opt-in for testing
merge_confidence_weight: float = 0.1     # Small contribution to fusion
```

### Expected Outcomes

1. **Stability Improvement**: 30-50% reduction in false positives from hand jitter
2. **Distance Consistency**: More uniform detection reliability across near/far ranges  
3. **Robustness**: Better handling of poor lighting and partial occlusions
4. **Adaptability**: Automatic adjustment to different cameras and environments
5. **Smoothness**: Fewer spurious state transitions from noise

### Implementation Priority

1. **Noise calibration** (foundation for other improvements)
2. **Logistic scoring functions** (immediate stability boost)
3. **Dynamic k_d/k_theta** (better distance handling)
4. **Expanded MFC triggers** (fill detection gaps)
5. **Confidence weighting** (robustness to poor tracking)
6. **Temporal smoothing** (if still seeing noise issues)
7. **Merge confidence** (optional enhancement)

### Data Requirements

#### Phase 1-2: No Training Data Needed
These improvements are **algorithmic only** - they don't require any training data:
- Logistic scoring functions are mathematical transformations
- Noise calibration is self-adaptive per session
- Dynamic coefficients use formulas, not learned parameters
- All improvements work immediately without data collection

#### Validation Data (Optional but Recommended)
While not required for implementation, collecting ground truth data helps measure improvement:

```python
# Simple validation data collector
def collect_validation_data(touchproof_detector, frame, landmarks):
    """Collect labeled examples for measuring improvement"""
    signals = touchproof_detector.update(landmarks, frame, width, height)
    
    # User labels with arrow keys
    key = cv2.waitKey(1) & 0xFF
    if key == 82:  # Up arrow - touching
        return {'signals': signals.__dict__, 'ground_truth': True, 'timestamp': time.time()}
    elif key == 84:  # Down arrow - not touching
        return {'signals': signals.__dict__, 'ground_truth': False, 'timestamp': time.time()}
    return None
```

**Recommended validation dataset size**: 100-200 labeled examples covering:
- Various distances (near/medium/far)
- Different hand orientations
- Edge cases (barely touching, just separated)

#### Phase 3: Would Require Training Data
Future ML-based improvements would need:
- 1000+ labeled touch/no-touch examples
- Per-user calibration sequences
- Diverse lighting and camera conditions

### Testing Strategy

1. **Baseline metrics**: Record current false positive/negative rates at various distances
2. **A/B testing**: Toggle improvements individually to measure impact
3. **Stress testing**: Low light, fast movement, partial occlusions
4. **User testing**: Multiple hand sizes and skin tones
5. **Long-term stability**: Extended sessions to verify calibration holds

### Implementation Notes

**Important**: Phase 1-2 improvements can be implemented immediately without any data collection. The validation data is only to prove the improvements work better than the current system.

### Future Considerations

For a potential Phase 3:
- Learnable monotonic mapping from signals to fused score
- Per-user calibration profiles
- Bayesian fusion with proper uncertainty propagation
- Integration with gesture context (e.g., different thresholds during/after gestures)

## Conclusion

These improvements maintain the elegant architecture of the current TouchProof system while addressing its main limitations. The phased approach allows for incremental validation and rollback if needed. Most importantly, the system becomes self-adaptive rather than relying on fixed parameters tuned for specific conditions.