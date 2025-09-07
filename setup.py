"""Setup script for Glide package."""

from setuptools import find_packages, setup

setup(
    name="glide",
    version="0.1.0",
    description="Advanced fingertip gesture control with TouchProof detection",
    packages=find_packages(),
    python_requires=">=3.10",
    install_requires=[
        "numpy",
        "opencv-python",
        "mediapipe",
        "PyYAML",
    ],
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
)
