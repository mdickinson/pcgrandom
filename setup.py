# Copyright 2017 Mark Dickinson
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from setuptools import find_packages, setup

long_description = """
Random classes based on the PCG family of generators.

Provides a PCG-based drop-in replacement for Python's random.Random.
"""

setup(
    name="pcgrandom",
    version='0.0.0',
    description="Random classes based on the PCG family of generators",
    long_description=long_description,
    url="https://github.com/mdickinson/pcgrandom",
    author="Mark Dickinson",
    author_email="dickinsm@gmail.com",
    license="Apache license",
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Intended Audience :: Science/Research",
        "License :: OSI Approved :: Apache Software License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 2",
        "Programming Language :: Python :: 2.7",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.3",
        "Programming Language :: Python :: 3.4",
        "Programming Language :: Python :: 3.5",
        "Programming Language :: Python :: 3.6",
        "Topic :: Scientific/Engineering",
    ],
    keywords="PCG PRNG RNG random",
    packages=find_packages(),
    install_requires=["future"],
    python_requires=">=2.7, !=3.0.*, !=3.1.*, !=3.2.*",
    package_data={},
)
