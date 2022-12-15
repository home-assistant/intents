#!/usr/bin/env python3
from pathlib import Path

import setuptools
from setuptools import setup

this_dir = Path(__file__).parent
module_dir = this_dir / "hassil"

# -----------------------------------------------------------------------------

# Load README in as long description
long_description: str = ""
readme_path = this_dir / "README.md"
if readme_path.is_file():
    long_description = readme_path.read_text(encoding="utf-8")

requirements = []
requirements_path = this_dir / "requirements.txt"
if requirements_path.is_file():
    with open(requirements_path, "r", encoding="utf-8") as requirements_file:
        requirements = requirements_file.read().splitlines()

version_path = module_dir / "VERSION"
with open(version_path, "r", encoding="utf-8") as version_file:
    version = version_file.read().strip()

# -----------------------------------------------------------------------------

setup(
    name="hassil",
    version=version,
    description="The Home Assistant Intent Language parser",
    long_description=long_description,
    url="http://github.com/rhasspy/hassil",
    author="Michael Hansen",
    author_email="mike@rhasspy.org",
    license="Apache-2.0",
    packages=setuptools.find_packages(),
    package_data={
        "hassil": ["VERSION", "py.typed"],
    },
    install_requires=requirements,
    extras_require={':python_version<"3.9"': ["importlib_resources"]},
    entry_points={
        "console_scripts": [
            "hassil = hassil.__main__:main",
        ]
    },
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Topic :: Text Processing :: Linguistic",
        "License :: OSI Approved :: License :: OSI Approved :: Apache Software License",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
    ],
    keywords="home assistant intent recognition",
)
