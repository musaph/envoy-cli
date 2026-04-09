"""Setup configuration for envoy-cli."""

from setuptools import setup, find_packages
from pathlib import Path

# Read the contents of README file
this_directory = Path(__file__).parent
long_description = (this_directory / "README.md").read_text(encoding="utf-8")

setup(
    name="envoy-cli",
    version="0.1.0",
    description="A CLI tool for managing and syncing .env files across environments using encrypted remote stores",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="Envoy CLI Team",
    author_email="team@envoy-cli.dev",
    url="https://github.com/envoy-cli/envoy-cli",
    packages=find_packages(exclude=["tests", "tests.*"]),
    python_requires=">=3.7",
    install_requires=[
        "cryptography>=41.0.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.4.0",
            "pytest-cov>=4.1.0",
            "black>=23.7.0",
            "flake8>=6.1.0",
            "mypy>=1.5.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "envoy=envoy.cli:main",
        ],
    },
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Build Tools",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    keywords="env environment variables encryption sync clienv",
    project_urls={
        "Bug Reports": "https://github.com/envoy-cli/envoy-cli/issues",
        "Source": "httpscli/envoy-cli",
    },
)
