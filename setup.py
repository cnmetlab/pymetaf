import setuptools
import os

FILE_PATH = os.path.dirname(os.path.realpath(__file__))

with open(os.path.join(FILE_PATH, "README.md"), "r") as fh:
    long_description = fh.read()

requirements_path = os.path.join(FILE_PATH, "requirements.txt")
with open(requirements_path) as f:
    required = f.read().splitlines()

# 从 pymetaf/__init__.py 读取版本号
version = {}
with open(os.path.join(FILE_PATH, "pymetaf", "__init__.py")) as f:
    for line in f:
        if line.startswith("__version__"):
            exec(line, version)
            break

setuptools.setup(
    name="pymetaf",
    version=version["__version__"],
    author="Wentao Li",
    author_email="clarmyleewt@outlook.com",
    description="A python package for parsing metar & taf raw text",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/Clarmy/pymetaf",
    include_package_data=True,
    package_data={"": ["*.csv", "*.config", "*.nl", "*.json"]},
    packages=setuptools.find_packages(),
    install_requires=required,
    classifiers=[
        "Programming Language :: Python :: 3",
    ],
    python_requires=">=3.7",
)
