import setuptools

from als_to_midi import __description__, __author_email__, __author__, \
    __version__

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="als_to_midi-kovaacs",
    version=__version__,
    author=__author__,
    author_email=__author_email__,
    description=__description__,
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/kovaacs/als_to_mid",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3.6",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.6',
    scripts=["bin/als2midi.py"]
)
