import os
from setuptools import setup, find_packages

setup(
    name="lxpkg",
    version="1.2.7",
    packages=find_packages(),
    install_requires=["colorama"],
    entry_points={
        "console_scripts": [
            "lxpkg=src.main:main"
        ]
    },
    package_data={
        "src": ["*.py"]
    },
    author="LearnixOS",
    description="A lightweight package manager for lxos",
    long_description=open("README.md").read() if os.path.exists("README.md") else "",
    long_description_content_type="text/markdown",
    url="https://learnixos.github.io",
)
