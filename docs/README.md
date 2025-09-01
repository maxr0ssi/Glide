# Glide Documentation

Welcome to the Glide documentation! This directory contains technical documentation for developers and contributors.

## Documentation Index

### Core Documentation

- **[Architecture Overview](ARCHITECTURE.md)** - System architecture, components, and design principles
- **[TouchProof](TOUCHPROOF.md)** - Advanced fingertip contact detection algorithm

### Design Documents

- **[Original Design](designs/glide/DESIGN.md)** - Reference architecture and component specifications

## Quick Links

### For Users
- [Installation Guide](../README.md#installation)
- [Configuration Reference](../glide/io/defaults.yaml)
- [Usage Examples](../README.md#usage)

### For Developers
- [Contributing Guidelines](../CONTRIBUTING.md) *(coming soon)*
- [API Reference](https://github.com/yourusername/glide/wiki) *(coming soon)*

## Overview

Glide uses advanced computer vision techniques to detect hand gestures through a regular webcam. The system is built around two core innovations:

1. **TouchProof** - A multi-signal fusion system that accurately detects when fingertips are touching, solving the challenging problem of inferring 3D contact from 2D images.

2. **Scale-Invariant Detection** - All measurements are normalized by hand size, allowing consistent detection whether the hand is 30cm or 100cm from the camera.

## Getting Started

1. Review the [Architecture](ARCHITECTURE.md) to understand the system design
2. Read about [TouchProof](TOUCHPROOF.md) for details on the touch detection algorithm
3. Check the [configuration file](../glide/io/defaults.yaml) for tuning parameters

## Contributing

We welcome contributions! Please ensure you understand the architecture before making changes. Key areas for contribution:

- Additional gesture types
- Performance optimizations
- Multi-hand support
- Platform-specific integrations

## License

This project is licensed under the GPL-3.0 License - see the [LICENSE](../LICENSE) file for details.