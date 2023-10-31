from setuptools import setup, find_packages

with open('README.md') as f:
    long_description = f.read()

version = '0.0.4'
description = 'A package that allows you to run SAGA GIS tools in a Python environment.'

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
    install_requires=[],
    keywords=['python', 'gis', 'SAGA GIS', 'saga_cmd', 'PySAGA'],
    classifiers=[
        'License :: OSI Approved :: MIT License',
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Science/Research',
        'Programming Language :: Python :: 3',
        'Operating System :: Unix',
        'Operating System :: Microsoft :: Windows',
    ],
    extras_require={
        'dev': ['twine >=4.0.2'],
    },
)
