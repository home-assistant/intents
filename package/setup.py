#!/usr/bin/env python3
from pathlib import Path

import setuptools
from setuptools import setup

this_dir = Path(__file__).parent
module_dir = this_dir / "home_assistant_intents"
data_dir = module_dir / "data"
version = "0.0.1"

data_paths = [
    str(json_path.relative_to(module_dir)) for json_path in data_dir.rglob("*.json")
]

# -----------------------------------------------------------------------------

setup(
    name="home-assistant-intents",
    version=version,
    description="Intents for Home Assistant",
    url="http://github.com/home-assistant/intents",
    author="Michael Hansen",
    author_email="mike@rhasspy.org",
    license="Apache-2.0",
    packages=setuptools.find_packages(),
    package_data={
        "home_assistant_intents": data_paths,
    },
    extras_require={':python_version<"3.9"': ["importlib_resources"]},
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Topic :: Text Processing :: Linguistic",
        "License :: OSI Approved :: Apache Software License",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
    ],
    keywords="home assistant intent recognition",
)
