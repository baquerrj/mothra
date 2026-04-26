from setuptools import find_packages, setup

setup(
    name="simple-account-viewer",
    version="0.1.0",
    description="Local-only spending visualizer for checking account CSV files.",
    long_description=open("README.md", encoding="utf-8").read(),
    long_description_content_type="text/markdown",
    python_requires=">=3.10",
    packages=find_packages(include=["spending_visualizer", "spending_visualizer.*"]),
    install_requires=[
        "pandas>=2.2,<3.0",
        "streamlit>=1.44,<2.0",
    ],
    extras_require={
        "dev": [
            "mypy>=1.11,<2.0",
            "pytest>=8.3,<9.0",
            "ruff>=0.11,<0.12",
        ]
    },
)
