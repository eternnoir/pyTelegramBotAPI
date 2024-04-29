import os
import re

from setuptools import find_packages, setup


def get_version(package):
    """
    Return package version as listed in `__version__` in `init.py`.
    """
    with open(os.path.join(package, "__init__.py")) as f:
        return re.search("__version__ = ['\"]([^'\"]+)['\"]", f.read()).group(1)


def get_long_description():
    """
    Return the README.
    """
    with open("README.md", encoding="utf8") as f:
        return f.read()


setup(
    name="telegram-bale-bot",
    version="4.17.2",
    python_requires=">=3.8",
    url="https://github.com/mahdikiani/telegram-bale-bot",
    license="GPL2",
    description="A simple and easy-to-use library for creating Telegram bots and Bale messenger bots.",
    long_description=get_long_description(),
    long_description_content_type="text/markdown",
    author="Mahdi Kiani",
    author_email="mahdikiany@gmail.com",
    packages=find_packages(),
    zip_safe=False,
)
