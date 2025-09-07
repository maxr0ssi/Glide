"""Setup script for Glide package."""

import sys
from setuptools import find_packages, setup

# Base dependencies (cross-platform)
install_requires = [
    "numpy>=1.24.3,<2.0.0",
    "opencv-python>=4.8.1.78",
    "mediapipe>=0.10.8,<0.11.0",
    "PyYAML>=6.0.1",
    "pydantic>=2.5.3",
    "websockets>=12.0",
]

# Add macOS-specific dependencies
if sys.platform == "darwin":
    install_requires.extend(
        [
            "pyobjc-framework-Quartz>=10.1",
            "pyobjc-framework-Cocoa>=10.1",
        ]
    )

setup(
    name="glide",
    version="0.1.0",
    description="Advanced fingertip gesture control with TouchProof detection",
    long_description="Glide is a macOS application for advanced fingertip gesture control with TouchProof detection. It enables natural hand tracking and continuous scrolling using your camera.",
    long_description_content_type="text/plain",
    author="Glide Contributors",
    python_requires=">=3.10",
    packages=find_packages(),
    install_requires=install_requires,
    extras_require={
        "dev": [
            "ruff>=0.7.0",
            "black>=24.8.0",
            "mypy>=1.11.0",
            "pytest>=8.3.0",
            "pytest-asyncio>=0.24.0",
            "pre-commit>=3.8.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "glide=glide.app.main:main",
        ],
    },
    package_data={
        "glide": ["io/defaults.yaml"],  # Keep for backwards compatibility
    },
    data_files=[
        ("configs", ["configs/defaults.yaml"]),
    ],
    classifiers=[
        "Development Status :: 4 - Beta",
        "Environment :: MacOS X",
        "Intended Audience :: End Users/Desktop",
        "License :: OSI Approved :: MIT License",
        "Operating System :: MacOS :: MacOS X",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Human Machine Interfaces",
        "Topic :: Software Development :: User Interfaces",
    ],
)
