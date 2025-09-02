# Glide Documentation

Welcome to the Glide documentation! This directory contains technical documentation for developers and contributors.

## Documentation Index

### Core Documentation

- **[Architecture Overview](Architecture.md)** - System architecture, components, and design principles
- **[TouchProof](TouchProof.md)** - Advanced fingertip contact detection algorithm
- **[Scrolling Guide](Scrolling.md)** - How to use the macOS scrolling feature
- **[API Reference](Api.md)** - Developer API documentation
- **[Dependencies](Dependencies.md)** - External dependencies and requirements

## Quick Links

### For Users
- [Installation Guide](../README.md#installation)
- [Configuration Reference](../glide/io/defaults.yaml)
- [Usage Examples](../README.md#usage)

### For Developers
- [API Reference](Api.md)

## Overview

Glide uses advanced computer vision techniques to detect hand gestures through a regular webcam. The system is built around two core innovations:

1. **TouchProof** - A multi-signal fusion system that accurately detects when fingertips are touching, solving the challenging problem of inferring 3D contact from 2D images.

2. **Scale-Invariant Detection** - All measurements are normalized by hand size, allowing consistent detection whether the hand is 30cm or 100cm from the camera.

## Getting Started

1. Review the [Architecture](Architecture.md) to understand the system design
2. Read about [TouchProof](TouchProof.md) for details on the touch detection algorithm
3. Learn about [Scrolling](Scrolling.md) to use gesture-based scrolling
4. Check the [configuration file](../glide/io/defaults.yaml) for tuning parameters

## License

This project is licensed under the GPL-3.0 License - see the [LICENSE](../LICENSE) file for details.