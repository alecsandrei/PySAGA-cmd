import io
from os import path as op
from setuptools import setup, find_packages


with open('README.md') as f:
    long_description = f.read()

here = op.abspath(op.dirname(__file__))

version = '0.0.5'
description = 'A package that allows you to run SAGA GIS tools in a Python environment.'

with io.open(op.join(here, "requirements.txt"), encoding="utf-8") as f:
    core_reqs = f.read().split("\n")


extras_requires = {
        'dev': ['twine >=4.0.2'],
}

setup(
    name='PySAGA-cmd',
    version=version,
    author='Cuvuliuc Alex-Andrei',
    author_email="<cuvuliucalexandrei@gmail.com>",
    description=description,
    long_description=long_description,
    long_description_content_type='text/markdown',
    url='https://github.com/alecsandrei/PySAGA-cmd',
    packages=find_packages(),
    install_requires=core_reqs,
    extras_require=extras_requires,
    keywords=['python', 'gis', 'SAGA GIS', 'saga_cmd', 'PySAGA'],
    classifiers=[
        'License :: OSI Approved :: MIT License',
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Science/Research',
        'Programming Language :: Python :: 3',
        'Operating System :: Unix',
        'Operating System :: Microsoft :: Windows',
    ],
)
