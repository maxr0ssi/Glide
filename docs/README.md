# Glide Documentation

Welcome to the Glide documentation! This directory contains technical documentation for developers and contributors.

## Documentation Index

### Core Documentation

- **[Architecture Overview](ARCHITECTURE.md)** - System architecture, components, and design principles
- **[API Reference](Api.md)** - Developer API documentation
- **[Dependencies](DEPENDENCIES.md)** - External dependencies and requirements
- **[Scrolling Guide](Scrolling.md)** - Velocity-based scrolling implementation
- **[Velocity Scrolling](VelocityScrolling.md)** - Technical details on velocity tracking

### Algorithm Deep-Dives

- **[TouchProof Algorithm](algorithms/touchproof.md)** - Fingertip contact detection algorithm
- **[Mathematical Foundations](algorithms/math.md)** - Geometric calculations and signal processing

## Quick Links

### For Users
- [Installation Guide](../README.md#installation)
- [Configuration Reference](../glide/io/defaults.yaml)
- [Usage Examples](../README.md#usage)

### For Developers
- [API Reference](Api.md)

## Overview

Glide uses computer vision to detect hand gestures through a regular webcam. The system is built around two key ideas:

1. **TouchProof** - A multi-signal fusion system that detects when fingertips are touching, figuring out 3D contact from 2D camera images.

2. **Scale-Invariant Detection** - All measurements are normalized by hand size, allowing consistent detection whether the hand is 30cm or 100cm from the camera.

## Getting Started

1. Review the [Architecture](ARCHITECTURE.md) to understand the system design
2. Read about [TouchProof](algorithms/touchproof.md) for details on the touch detection algorithm
3. Learn about [Scrolling](Scrolling.md) to use gesture-based scrolling
4. Check the [configuration file](../glide/io/defaults.yaml) for tuning parameters

## License

This project is licensed under the GPL-3.0 License - see the [LICENSE](../LICENSE) file for details.
