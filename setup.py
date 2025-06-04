#!/usr/bin/env python3
"""
Setup script for pCloud SDK Python v1.0
"""

import os

from setuptools import find_packages, setup


def read_file(filename):
    """Read file content"""
    with open(os.path.join(os.path.dirname(__file__), filename), encoding="utf-8") as f:
        return f.read()


def read_requirements(filename):
    """Read requirements from file"""
    try:
        with open(filename, "r", encoding="utf-8") as f:
            return [
                line.strip() for line in f if line.strip() and not line.startswith("#")
            ]
    except FileNotFoundError:
        return []


setup(
    name="pcloud-sdk-python",
    version="1.0.0",
    author="pCloud SDK Python Contributors (Koffi joel)",
    author_email="jolli644@gmail.com",
    description="Modern Python SDK for pCloud API with automatic token management and progress tracking",
    long_description=read_file("README.md"),
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/pcloud-sdk-python",
    project_urls={
        "Bug Reports": "https://github.com/yourusername/pcloud-sdk-python/issues",
        "Source": "https://github.com/yourusername/pcloud-sdk-python",
        "Documentation": "https://pcloud-sdk-python.readthedocs.io/",
    },
    packages=find_packages(),
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Internet :: WWW/HTTP",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: System :: Filesystems",
        "Topic :: System :: Archiving :: Backup",
        "Topic :: Utilities",
    ],
    python_requires=">=3.7",
    install_requires=read_requirements("requirements.txt"),
    extras_require={
        "dev": ["flake8", "black", "isort", "mypy", "pre-commit", "twine", "build"],
        "test": ["pytest", "pytest-cov", "pytest-mock", "responses"],
        "docs": ["sphinx", "sphinx-rtd-theme", "myst-parser"],
    },
    entry_points={
        "console_scripts": [
            "pcloud-sdk=pcloud_sdk.cli:main",
        ],
    },
    keywords=[
        "pcloud",
        "api",
        "sdk",
        "cloud",
        "storage",
        "file",
        "upload",
        "download",
        "backup",
        "sync",
        "progress",
        "token",
        "oauth2",
        "rest",
    ],
    include_package_data=True,
    zip_safe=False,
)
