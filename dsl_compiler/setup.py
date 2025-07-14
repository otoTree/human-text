"""
Setup script for Human-Text DSL Compiler
"""

from setuptools import setup, find_packages
from pathlib import Path

# Read README for long description
readme_path = Path(__file__).parent / "README.md"
long_description = readme_path.read_text(encoding="utf-8") if readme_path.exists() else ""

# Read requirements
requirements_path = Path(__file__).parent / "requirements.txt"
requirements = []
if requirements_path.exists():
    with open(requirements_path, 'r', encoding='utf-8') as f:
        requirements = [
            line.strip() 
            for line in f 
            if line.strip() and not line.startswith('#')
        ]

setup(
    name="dsl-compiler",
    version="1.0.0",
    author="Super Context Team",
    author_email="team@supercontext.ai",
    description="A powerful compiler that converts human-readable text into structured DSL",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/otoTree/human-text",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Software Development :: Compilers",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Text Processing :: Linguistic",
    ],
    python_requires=">=3.8",
    install_requires=requirements,
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-asyncio>=0.21.0",
            "pytest-cov>=4.0.0",
            "black>=23.0.0",
            "flake8>=6.0.0",
            "mypy>=1.0.0",
            "pre-commit>=3.0.0",
        ],
        "docs": [
            "sphinx>=6.0.0",
            "sphinx-rtd-theme>=1.3.0",
            "sphinx-autodoc-typehints>=1.23.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "dslc=dsl_compiler.cli:main",
        ],
    },
    include_package_data=True,
    package_data={
        "dsl_compiler": [
            "*.example",
            "*.md",
            "requirements.txt",
        ],
    },
    keywords=[
        "dsl",
        "compiler",
        "natural-language",
        "llm",
        "text-processing",
        "yaml",
        "json",
        "protobuf",
        "automation",
        "workflow",
    ],
    project_urls={
        "Bug Reports": "https://github.com/otoTree/human-text/issues",
        "Source": "https://github.com/otoTree/human-text",
        "Documentation": "waiting for docs",
    },
) 